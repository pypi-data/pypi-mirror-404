from typing import Dict, Tuple, Union
from feasytools import TimeFunc
from .solbase import DEFAULT_SAVETO, IslandResult, SolverBase
from .grid import Grid
from .island import Island


def _parse(x, t:int):
    if x is None: raise ValueError("Cannot be None")
    if isinstance(x, (int, float)): return x
    if isinstance(x, TimeFunc): return x(t)
    raise TypeError("Unsupported type for parsing")

class LinDistFlow2Solver(SolverBase):
    def __init__(self, grid:Grid, eps:float = 1e-6, max_iter:int = 1000, *, default_saveto:str = DEFAULT_SAVETO):
        super().__init__(grid, eps, max_iter, default_saveto=default_saveto)
    
    def solve_island(self, i:int, island:Island, _t:int, **kwargs) -> Tuple[IslandResult, float]:
        from .lpwrapper import LinProgProblem, quicksum, _LPVar
        prob = LinProgProblem()

        obj = 0
        # Bind GEN vars to Bus
        pg0: 'dict[str, _LPVar]' = {}
        qg0: 'dict[str, _LPVar]' = {}
        pg: 'dict[str, list]' = {b: [] for b in island.Buses}
        qg: 'dict[str, list]' = {b: [] for b in island.Buses}
        qg_abs: 'dict[str, list]' = {b: [] for b in island.Buses}
        pd: 'dict[str, float]' = {bID: b.Pd(_t) for bID, b in island.BusItems()}
        qd: 'dict[str, float]' = {bID: b.Qd(_t) for bID, b in island.BusItems()}

        # Collect power generation data and set objective
        for gID, g in island.GenItems():
            if g.FixedP:
                pd[g.BusID] -= _parse(g.P, _t)
            else:
                p = prob.add_var(f"Pg_{gID}", _parse(g.Pmin, _t), _parse(g.Pmax, _t))
                pg[g.BusID].append(p)
                pg0[gID] = p
                obj = p * _parse(g.CostB, _t) + g.CostC(_t) + obj
            if g.FixedQ:
                qd[g.BusID] -= _parse(g.Q, _t)
            else:
                q = prob.add_var(f"Qg_{gID}", _parse(g.Qmin, _t), _parse(g.Qmax, _t))
                q_abs = prob.add_var(f"Qg_abs_{gID}", 0, None)
                qg[g.BusID].append(q)
                qg_abs[g.BusID].append(q_abs)
                prob.add_cons(q_abs >= q)
                prob.add_cons(q_abs >= -q)
                obj = q_abs * _parse(g.CostB, _t) * 0.1 + obj  # Assuming reactive power cost is 10% of active power cost
                qg0[gID] = q
                # Assuming no cost for reactive power generation
        
        # Collect power generation data for PV and ESS
        pv0: 'dict[str, _LPVar]' = {}

        for pID, p in island.PVWItems():
            p_var = prob.add_var(f"P_pv_{pID}", 0, p.P(_t))
            pv0[pID] = p_var
            pg[p.BusID].append(p_var)
            qg[p.BusID].append(p_var * p.PF)
        
        for eID, e in island.ESSItems():
            p, q = e.GetLoad(_t, island.grid.ChargePrice(_t), island.grid.DischargePrice(_t))
            e.P = p
            if p > 0:
                pd[e.BusID] += p
                qd[e.BusID] += q
            elif p < 0:
                pg[e.BusID].append(-p)
                qg[e.BusID].append(-q)
        
        # Create p,q vars for lines
        pl:Dict[str, _LPVar] = {}
        ql:Dict[str, _LPVar] = {}
        l2:Dict[str, _LPVar] = {}
        for lid, l in island.LineItems():
            pl[lid] = prob.add_var(f"p_{l.ID}", None, None)
            ql[lid] = prob.add_var(f"q_{l.ID}", None, None)
            l2[lid] = prob.add_var(f"l2_{l.ID}")
        
        # Create voltage vars for buses
        v2:Dict[str, Union[float, _LPVar]] = {}
        for bID, b in island.BusItems():
            if not b.FixedV:
                v2[bID] = prob.add_var(f"v2_{bID}", b.MinV ** 2, b.MaxV ** 2)
            else:
                assert b.V is not None
                v2[bID] = b.V ** 2

        # Add power constraints for each bus
        for j, bus in island.BusItems():
            flow_in = island.grid.LinesOfTBus(j)
            flow_out = island.grid.LinesOfFBus(j)
            
            # P constraint
            inflow = quicksum(pl[ln.ID] for ln in flow_in if ln.ID in island.Lines)
            outflow = quicksum(pl[ln.ID] for ln in flow_out if ln.ID in island.Lines)
            prob.add_cons(inflow + quicksum(pg[j]) == outflow + pd[j])

            # flow_in and flow_out are Python generators, which cannot be reused, thus needed to be re-assigned
            flow_in = island.grid.LinesOfTBus(j)
            flow_out = island.grid.LinesOfFBus(j)
            # Q constraint
            q_inflow = quicksum(ql[ln.ID] for ln in flow_in if ln.ID in island.Lines)
            q_outflow = quicksum(ql[ln.ID] for ln in flow_out if ln.ID in island.Lines)
            prob.add_cons(q_inflow + quicksum(qg[j]) == q_outflow + qd[j])
        
        # Add line constraints
        for lid, l in island.LineItems():
            fbus = island.grid.Bus(l.fBus)
            tbus = island.grid.Bus(l.tBus)
            if fbus is None or tbus is None:
                raise ValueError(f"Line {l.ID} has no bus {l.fBus} or {l.tBus}")
            prob.add_cons(v2[tbus.ID] == v2[fbus.ID] - 2*l.R*pl[lid] - 2*l.X*ql[lid])
            l.I = None # Clear the current variable to avoid confusion

        prob.set_objective(obj)
        status, obj = prob.solve(minimize=True)
        if status == 0: 
            # Solution found
            for lid, l in island.LineItems():
                l.P = pl[lid].x
                l.Q = ql[lid].x
                this_I2 = l2[lid]
                if this_I2.x is not None:
                    l.I = this_I2.x ** 0.5

            for bID, b in island.BusItems():
                this_v2 = v2[bID]
                if isinstance(this_v2, _LPVar) and this_v2.x is not None:
                    b.V = this_v2.x ** 0.5
                b.theta = 0.0 # Angle is not calculated in LinDistFlow
            
            for gID, g in island.GenItems():
                if not g.FixedP:
                    g._p = pg0[gID].x
                if not g.FixedQ:
                    g._q = qg0[gID].x
            
            for pID, p in island.PVWItems():
                p._pr = pv0[pID].x
                p._qr = p._pr * p.PF if p._pr is not None else 0
            
            return IslandResult.OK, obj
        else:
            return IslandResult.Failed, obj

__all__ = ['LinDistFlow2Solver']