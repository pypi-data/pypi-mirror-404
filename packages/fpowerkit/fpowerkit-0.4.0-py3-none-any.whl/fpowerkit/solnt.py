import numpy as np
from typing import Any
from feasytools import TimeFunc
from enum import IntEnum
from dataclasses import dataclass
from .grid import BusID, Grid
from .island import Island, IslandResult
from .solbase import *

class BusType(IntEnum):
    PQ = 0
    PV = 1
    Slack = 2

@dataclass
class _NRProblem:
    eqs: 'list[int]'
    n_P: int
    Ps: np.ndarray # list[float]
    Qs: np.ndarray # list[float]
    bus_dict: 'dict[str, int]'
    G: np.ndarray # 2D
    B: np.ndarray # 2D
    V: np.ndarray # list[float]
    theta: np.ndarray # list[float]
    slack: int

def _presolve(il:Island, _t:int):
    '''Check the bus type'''
    busType: 'dict[BusID, BusType]' = {}
    slack_cnt = 0
    eq_P: 'list[int]' = []
    eq_Q: 'list[int]' = []
    V: 'list[float]' = []
    theta: 'list[float]' = []
    Ps: 'list[float]' = []
    Qs: 'list[float]' = []
    slack:int = -1
    bus_dict, Y = il.YMat()
    for bid, i in bus_dict.items():
        bus = il.grid.Bus(bid)
        V.append(bus.V if bus.V is not None else 1.0)
        theta.append(bus.theta if bus.theta is not None else 0.0)
        fixp = fixq = True
        p = -bus.Pd(_t)
        q = -bus.Qd(_t)
        for g in il.grid.GensAtBus(bus.ID):
            if not g.FixedP: fixp = False
            else:
                assert g.P is not None
                if isinstance(g.P, TimeFunc): p += g.P(_t)
                else: p += g.P
            if not g.FixedQ: fixq = False
            else:
                assert g.Q is not None
                if isinstance(g.Q, TimeFunc): q += g.Q(_t)
                else: q += g.Q
        if bus.FixedV:
            if fixp and fixq:
                raise ValueError(f"Bus {bus.ID}: Invalid bus type PQV")
            elif fixp:
                busType[bus.ID] = BusType.PV
                eq_P.append(i)
            elif fixq:
                raise ValueError(f"Bus {bus.ID}: Invalid bus type VQ")
            else:
                busType[bus.ID] = BusType.Slack
                slack = i
                slack_cnt += 1
                if slack_cnt > 1:
                    raise ValueError('Only one slack bus is allowed')
        else:
            if fixp and fixq:
                busType[bus.ID] = BusType.PQ
                bus.V = 1.0
                eq_P.append(i)
                eq_Q.append(i)
            elif fixp:
                raise ValueError(f"Bus {bus.ID}: Invalid bus type: Pθ")
            elif fixq:
                raise ValueError(f"Bus {bus.ID}: Invalid bus type: Qθ")
            else:
                raise ValueError(f"Bus {bus.ID}: Invalid bus type: θ")
        Ps.append(p)
        Qs.append(q)
    if slack_cnt == 0:
        raise ValueError('No slack bus is found')
    return _NRProblem(
        eq_P + eq_Q, len(eq_P), np.asarray(Ps), np.asarray(Qs), 
        bus_dict, Y.real, Y.imag, np.asarray(V), np.asarray(theta), slack
    )

def _presolve2(il:Island, _t:int):
    '''Check the bus type after using distflow-like algorithm'''
    busType: 'dict[BusID, BusType]' = {}
    slack_cnt = 0
    eq_P: 'list[int]' = []
    eq_Q: 'list[int]' = []
    V: 'list[float]' = []
    theta: 'list[float]' = []
    Ps: 'list[float]' = []
    Qs: 'list[float]' = []
    bus_dict, Y = il.YMat()
    slack = -1

    for bid, i in bus_dict.items():
        bus = il.grid.Bus(bid)
        V.append(bus.V if bus.V is not None else 1.0)
        theta.append(bus.theta if bus.theta is not None else 0.0)
        
        p = -bus.Pd(_t)
        q = -bus.Qd(_t)
        for g in il.grid.GensAtBus(bus.ID):
            assert g.P is not None
            if isinstance(g.P, TimeFunc): p += g.P(_t)
            else: p += g.P

            assert g.Q is not None
            if isinstance(g.Q, TimeFunc): q += g.Q(_t)
            else: q += g.Q

        if bus.FixedV:
            # After Distflow presolve, all the output of generator are fixed, except for the source bus whose V is fixed.
            busType[bus.ID] = BusType.Slack
            slack_cnt += 1
            slack = i
            if slack_cnt > 1:
                raise ValueError('Only one slack bus is allowed')
        else:
            # All other nodes are treated as PQ
            
            busType[bus.ID] = BusType.PQ
            bus.V = 1.0
            eq_P.append(i)
            eq_Q.append(i)

        Ps.append(p)
        Qs.append(q)
    
    if slack_cnt == 0:
        raise ValueError('No slack bus is found')
    return _NRProblem(eq_P + eq_Q, len(eq_P), np.asarray(Ps), np.asarray(Qs), 
                      bus_dict, Y.real, Y.imag, np.asarray(V), np.asarray(theta), slack
                    )

def _solve(prb: _NRProblem, max_iter: int = 100, eps: float = 1e-6):
    # ---- unpack ----
    G = prb.G
    B = prb.B
    V = prb.V
    T = prb.theta

    eqs = np.array(prb.eqs, dtype=int)
    Ps = prb.Ps
    Qs = prb.Qs

    n_P = prb.n_P
    n = len(eqs)
    # m = len(V)

    # ---- helper: compute P, Q for all buses ----
    def calc_PQ():
        # angle difference matrix
        dT = T[:, None] - T[None, :]
        cosT = np.cos(dT)
        sinT = np.sin(dT)

        VmVn = V[:, None] * V[None, :]

        P:np.ndarray = np.sum(VmVn * (G * cosT + B * sinT), axis=1)
        Q:np.ndarray = np.sum(VmVn * (G * sinT - B * cosT), axis=1)
        return P, Q, cosT, sinT

    cnt = 0
    while cnt < max_iter:
        P, Q, cosT, sinT = calc_PQ()

        # ---- mismatch vector y ----
        y = np.empty(n)
        y[:n_P] = Ps[eqs[:n_P]] - P[eqs[:n_P]]
        y[n_P:] = Qs[eqs[n_P:]] - Q[eqs[n_P:]]

        if np.max(np.abs(y)) < eps:
            break

        cnt += 1

        # ---- Jacobian blocks ----
        VmVn = V[:, None] * V[None, :]

        # H = dP/dθ
        H = -(VmVn * (G * sinT - B * cosT))
        np.fill_diagonal(H, Q + V * V * B.diagonal())

        # N = dP/dV * V
        N = -(VmVn * (G * cosT + B * sinT)) # type: ignore
        np.fill_diagonal(N, -P - V * V * G.diagonal())

        # M = dQ/dθ
        M = VmVn * (G * cosT + B * sinT)
        np.fill_diagonal(M, -P + V * V * G.diagonal())

        # L = dQ/dV * V
        L = -(VmVn * (G * sinT - B * cosT))
        np.fill_diagonal(L, -Q + V * V * B.diagonal())

        # ---- assemble reduced Jacobian ----
        buses_P = eqs[:n_P]
        buses_Q = eqs[n_P:]

        J = np.block([
            [H[np.ix_(buses_P, buses_P)], N[np.ix_(buses_P, buses_Q)]],
            [M[np.ix_(buses_Q, buses_P)], L[np.ix_(buses_Q, buses_Q)]]
        ])

        # ---- solve ----
        dx = np.linalg.solve(J, -y)

        # ---- update state ----
        T[buses_P] += dx[:n_P]
        V[buses_Q] *= (1.0 + dx[n_P:])

    if cnt >= max_iter:
        raise ValueError("Bad solution")

    # ---- final injections ----
    P, Q, *_ = calc_PQ()
    return cnt, V, T, P, Q, prb.bus_dict


class NewtonSolver(SolverBase):
    def __init__(self, grid:Grid, eps:float = 1e-6, default_saveto:str = DEFAULT_SAVETO, max_iter:int = 100, is_cmb_calculator:bool = False):
        super().__init__(grid, eps, max_iter, default_saveto = default_saveto)
        self.__is_cmb_calc = is_cmb_calculator

    def solve_island(self, i:int, island:Island, _t:int, **kwargs) -> 'tuple[IslandResult, float]':
        try:
            if self.__is_cmb_calc:
                prb = _presolve2(island, _t)
            else:
                prb = _presolve(island, _t)
            cnt, V, theta, P_inject, Q_inject, bus_dict = _solve(prb, self.max_iter, self.eps)
        except ValueError as e:
            return IslandResult.Failed, 0.0
        
        for b, i in bus_dict.items():
            bus = island.grid.Bus(b)
            bus.V = V[bus_dict[b]].item()
            bus.theta = theta[bus_dict[b]].item()
            gens = self.grid.GensAtBus(b)
            if len(gens) == 0:
                continue
            pg = P_inject[i].item() + bus.Pd(_t)
            qg = Q_inject[i].item() + bus.Qd(_t)

            # Allocate the generation to minimize generation cost
            from .lpwrapper import LinProgProblem, quicksum
            prob = LinProgProblem()
            p_dict = {}; q_dict = {}; obj = 0
            for g in gens:
                if g.FixedP: 
                    if isinstance(g.P, TimeFunc):
                        pg -= g.P(_t)
                    else:
                        assert g.P is not None
                        pg -= g.P
                else:
                    assert g.Pmin is not None and g.Pmax is not None
                    p_dict[g.ID] = prob.add_var(f'pg_{g.ID}', lb=g.Pmin(_t), ub=g.Pmax(_t))
                    obj += g.CostB(_t) * p_dict[g.ID] + g.CostC(_t)
                if g.FixedQ:
                    if isinstance(g.Q, TimeFunc):
                        qg -= g.Q(_t)
                    else:
                        assert g.Q is not None
                        qg -= g.Q
                else:
                    assert g.Qmin is not None and g.Qmax is not None
                    q_dict[g.ID] = prob.add_var(f'qg_{g.ID}', lb=g.Qmin(_t), ub=g.Qmax(_t))
                    q_abs = prob.add_var(f'qg_abs_{g.ID}', lb=0.0)
                    prob.add_cons(q_abs >= q_dict[g.ID])
                    prob.add_cons(q_abs >= -q_dict[g.ID])
                    obj += g.CostB(_t) * q_abs * 0.1
            prob.add_cons(quicksum(p_dict.values()) == pg)
            prob.add_cons(quicksum(q_dict.values()) == qg)
            prob.set_objective(obj)
            prob.solve()
            for gid, var in p_dict.items():
                island.grid.Gen(gid)._p = var.x
            for gid, var in q_dict.items():
                island.grid.Gen(gid)._q = var.x

        return IslandResult.OK, 0.0

__all__ = ['NewtonSolver', 'BusType']