from typing import Dict, Optional, Tuple, Union
from feasytools import TimeFunc
from .solbase import DEFAULT_SAVETO, IslandResult, SolverBase
from .grid import Grid
from .island import Island


def _parse(x, t:int):
    if x is None: raise ValueError("Cannot be None")
    if isinstance(x, (int, float)): return x
    if isinstance(x, TimeFunc): return x(t)
    raise TypeError("Unsupported type for parsing")

class LinDistFlowSolver(SolverBase):
    def __init__(self, grid:Grid, eps:float = 1e-6, max_iter:int = 1000, *,
            default_saveto:str = DEFAULT_SAVETO, solver = "ECOS"):
        super().__init__(grid, eps, max_iter, default_saveto=default_saveto)
        self.__solver = solver
    
    def solve_island(self, i:int, island:Island, _t:int, **kwargs) -> Tuple[IslandResult, float]:
        import cvxpy as cp
        cons = []
        obj = 0
        # Bind GEN vars to Bus
        pg0: 'dict[str, cp.Variable]' = {}
        qg0: 'dict[str, cp.Variable]' = {}
        pg: 'dict[str, list]' = {b: [] for b in island.Buses}
        qg: 'dict[str, list]' = {b: [] for b in island.Buses}
        pd: 'dict[str, float]' = {bID: b.Pd(_t) for bID, b in island.BusItems()}
        qd: 'dict[str, float]' = {bID: b.Qd(_t) for bID, b in island.BusItems()}

        # Collect power generation data and set objective
        for gID, g in island.GenItems():
            if g.FixedP:
                pd[g.BusID] -= _parse(g.P, _t)
            else:
                p = cp.Variable(name = f"Pg_{gID}", bounds=[_parse(g.Pmin, _t), _parse(g.Pmax, _t)])
                pg[g.BusID].append(p)
                pg0[gID] = p
                obj = p * _parse(g.CostA, _t) ** 2 + p * _parse(g.CostB, _t) + g.CostC(_t) + obj
            if g.FixedQ:
                qd[g.BusID] -= _parse(g.Q, _t)
            else:
                q = cp.Variable(name = f"Qg_{gID}", bounds=[_parse(g.Qmin, _t), _parse(g.Qmax, _t)])
                qg[g.BusID].append(q)
                qg0[gID] = q
                # Assuming no cost for reactive power generation
        
        # Collect power generation data for PV and ESS
        pv0: 'dict[str, cp.Variable]' = {}

        for pID, p in island.PVWItems():
            p_var = cp.Variable(name = f"P_pv_{pID}", bounds=[0, p.P(_t)])
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
        pl:Dict[str, cp.Variable] = {}
        ql:Dict[str, cp.Variable] = {}
        l2:Dict[str, cp.Variable] = {}
        for lid, l in island.LineItems():
            pl[lid] = cp.Variable(name = f"p_{l.ID}", bounds=[None, None])
            ql[lid] = cp.Variable(name = f"q_{l.ID}", bounds=[None, None])
            l2[lid] = cp.Variable(name = f"l2_{l.ID}", nonneg=True)

        # Create voltage vars for buses
        v2:Dict[str, Union[float, cp.Variable]] = {}
        for bID, b in island.BusItems():
            if not b.FixedV:
                v2[bID] = cp.Variable(name = f"v2_{bID}", bounds=[b.MinV ** 2, b.MaxV ** 2])
            else:
                assert b.V is not None
                v2[bID] = b.V ** 2

        # Add power constraints for each bus
        for j, bus in island.BusItems():
            flow_in = island.grid.LinesOfTBus(j)
            flow_out = island.grid.LinesOfFBus(j)
            
            # P constraint
            inflow = cp.sum([pl[ln.ID] for ln in flow_in if ln.ID in island.Lines])
            outflow = cp.sum([pl[ln.ID] for ln in flow_out if ln.ID in island.Lines])
            cons.append(inflow + cp.sum(pg[j]) == outflow + pd[j])

            # flow_in and flow_out are Python generators, which cannot be reused, thus needed to be re-assigned
            flow_in = island.grid.LinesOfTBus(j)
            flow_out = island.grid.LinesOfFBus(j)
            # Q constraint
            q_inflow = cp.sum([ql[ln.ID] for ln in flow_in if ln.ID in island.Lines])
            q_outflow = cp.sum([ql[ln.ID] for ln in flow_out if ln.ID in island.Lines])
            cons.append(q_inflow + cp.sum(qg[j]) == q_outflow + qd[j])
        
        # Add line constraints
        for lid, l in island.LineItems():
            fbus = island.grid.Bus(l.fBus)
            tbus = island.grid.Bus(l.tBus)
            if fbus is None or tbus is None:
                raise ValueError(f"Line {l.ID} has no bus {l.fBus} or {l.tBus}")
            cons.append(v2[tbus.ID] == v2[fbus.ID] - 2*l.R*pl[lid] - 2*l.X*ql[lid])
            l.I = None # Clear the current variable to avoid confusion

        prob = cp.Problem(cp.Minimize(obj), cons)
        prob.solve(solver=self.__solver, verbose=False, max_iters=self.max_iter)
        if prob.status in (cp.OPTIMAL, cp.OPTIMAL_INACCURATE):
            # Solution found
            for lid, l in island.LineItems():
                this_P = pl[lid].value
                if this_P is not None:
                    l.P = this_P.item()
                this_Q = ql[lid].value
                if this_Q is not None:
                    l.Q = this_Q.item()
                this_I2 = l2[lid].value
                if this_I2 is not None:
                    l.I = this_I2.item() ** 0.5

            for bID, b in island.BusItems():
                this_v2 = v2[bID]
                if isinstance(this_v2, cp.Variable) and this_v2.value is not None:
                    b.V = this_v2.value.item() ** 0.5
                b.theta = 0.0 # Angle is not calculated in LinDistFlow
            
            for gID, g in island.GenItems():
                if not g.FixedP:
                    this_pg = pg0[gID].value
                    if this_pg is not None:
                        g._p = this_pg.item()
                if not g.FixedQ:
                    this_qg = qg0[gID].value
                    if this_qg is not None:
                        g._q = this_qg.item()

            for pID, p in island.PVWItems():
                this_pr = pv0[pID].value
                if this_pr is not None:
                    p._pr = this_pr.item()
                p._qr = p._pr * p.PF if p._pr is not None else 0
            
            obj_out = prob.value
            assert isinstance(obj_out, (int, float))
            return IslandResult.OK, float(obj_out)
        else:
            return IslandResult.Failed, 0.0

__all__ = ['LinDistFlowSolver']