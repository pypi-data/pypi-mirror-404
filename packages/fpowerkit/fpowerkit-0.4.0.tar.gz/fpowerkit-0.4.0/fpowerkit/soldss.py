import math
from typing import Iterable, Union
from feasytools import TimeFunc
from .grid import Grid
from .solbase import *
from .island import Island, IslandResult

def _convert(il:Island, t:int, source_bus:str):
    try:
        from py_dss_interface import DSS
    except ImportError:
        raise ImportError("py_dss_interface or OpenDSS is not installed. Please install OpenDSS first and then py_dss_interface using 'pip install py_dss_interface'")

    try:
        d = DSS() # type: ignore
    except:
        d = DSS.DSSDLL() # type: ignore
    d.text("clear")
    Ub = il.grid.Ub
    Sb_MVA = il.grid.Sb_MVA
    Sb_kVA = il.grid.Sb_kVA
    Zb = il.grid.Zb
    cir = f"new circuit.my_circuit basekv={Ub} pu=1 MVASC3=5000000 5000000 bus1={source_bus}"
    assert source_bus in il.grid.BusNames, f"Source bus {source_bus} not found in the grid"
    d.text(cir)
    for bid, bus in il.BusItems():
        if bid != bid.lower():
            raise ValueError(f"Bus ID {bid} must be lower case")
        p = bus.Pd(t)
        q = bus.Qd(t)
        d.text(f"New Load.{bid} bus1={bid} kv={Ub} kW={p*Sb_kVA} kvar={q*Sb_kVA} vmin={bus.MinV} vmax={bus.MaxV}")
    for lid, line in il.LineItems():
        fid = line.fBus
        tid = line.tBus
        if lid != lid.lower():
            raise ValueError(f"Line ID {lid} must be lower case")
        d.text(f"New line.{lid} bus1={fid} bus2={tid} R1={line.R*Zb} units=ohm X1={line.X*Zb} units=ohm")
    for pid, pvw in il.PVWItems():
        if pid != pid.lower():
            raise ValueError(f"PVWind ID {pid} must be lower case")
        if pvw.Pr is None:
            raise ValueError(f"PVWind {pid} has no Pr value")
        p = pvw.Pr
        if pvw.Qr is None:
            raise ValueError(f"PVWind {pid} has no Qr value")
        q = pvw.Qr
        bid = pvw.BusID
        
        s = f"New Generator.{pvw.ID} bus1={bid} kv={Ub} kw={p*Sb_kVA} kvar={q*Sb_kVA}"
        d.text(s)
    for eid, ess in il.ESSItems():
        if eid != eid.lower():
            raise ValueError(f"ESS ID {eid} must be lower case")
        if ess.P is None:
            raise ValueError(f"ESS {eid} has no P value")
        p = ess.P
        if ess.Q is None:
            raise ValueError(f"ESS {eid} has no Q value")
        q = ess.Q
        bid = ess.BusID
        if p > 0: # charging = load
            bus = il.grid.Bus(bid)
            s = f"New Load.{ess.ID} bus1={bid} kv={Ub} kW={p*Sb_kVA} kvar={q*Sb_kVA} vmin={bus.MinV} vmax={bus.MaxV}"
        else: # discharging = generator
            s = f"New Generator.{ess.ID} bus1={bid} kv={Ub} kw={p*Sb_kVA} kvar={q*Sb_kVA}"
        d.text(s)
    for gid, gen in il.GenItems():
        if gid != gid.lower():
            raise ValueError(f"Generator ID {gid} must be lower case")
        bid = gen.BusID
        if gen.P is None and bid != source_bus:
            raise ValueError(f"Generator {gen.ID} has no P value")
        p = gen.P(t) if isinstance(gen.P, TimeFunc) else gen.P
        if gen.Q is None and bid != source_bus:
            raise ValueError(f"Generator {gen.ID} has no Q value")
        q = gen.Q(t) if isinstance(gen.Q, TimeFunc) else gen.Q
        
        s = f"New Generator.{gen.ID} bus1={bid} kv={Ub} "
        if p is not None:
            s+=f"kw={p*Sb_kVA} "
        if q is not None:
            s+=f"kvar={q*Sb_kVA}"
        d.text(s)
    d.text("set mode=snapshot")
    return d
    

class OpenDSSSolver(SolverBase):
    def UpdateGrid(self, grid: Grid):
        super().UpdateGrid(grid)
        self.__sbus:'list[str]' = []
        for il in self.Islands:
            b = self.source_buses.intersection(il.Buses)
            assert len(b) == 1, f"Source bus {self.source_buses} not found in an island"
            self.__sbus.append(b.pop())
    
    def __init__(self, grid:Grid, eps:float = 1e-6, max_iter:int = 1000, *, 
            default_saveto:str = DEFAULT_SAVETO, source_bus:'Union[str,Iterable[str]]'):
        if isinstance(source_bus, str): source_bus = [source_bus]
        assert isinstance(source_bus, Iterable), "source_bus must be a string or a list of strings"
        self.source_buses = set(source_bus)
        super().__init__(grid, eps, max_iter, default_saveto = default_saveto)

    def solve_island(self, il_no:int, il:Island, _t:int, /, *, timeout_s:float = 1) -> 'tuple[IslandResult, float]':
        self.dss = _convert(il, _t, self.__sbus[il_no])
        self.dss.text(f"set Voltagebases=[{self.grid.Ub}]")
        self.dss.text("calcv")
        self.dss.text("solve maxcontrol=10000")
        if hasattr(self.dss, "circuit"):
            bnames = self.dss.circuit.buses_names # type: ignore
            bvolt = np.array(self.dss.circuit.buses_volts).reshape(-1, 3, 2) # type: ignore
        else:
            bnames = self.dss.circuit_all_bus_names() # type: ignore
            bvolt = np.array(self.dss.circuit_all_bus_volts()).reshape(-1, 3, 2) # type: ignore
        sb_theta = 0
        for i, bn in enumerate(bnames):
            v1 = bvolt[i,0][0] + 1j * bvolt[i,0][1]
            v2 = bvolt[i,1][0] + 1j * bvolt[i,1][1]
            v = v1 - v2
            b = self.grid.Bus(bn)
            b._v = abs(v) / self.grid.Ub / 1000
            b.theta = math.atan2(v.imag, v.real)
            if bn == self.__sbus[il_no]:
                sb_theta = b.theta
        
        for i, bn in enumerate(bnames):
            self.grid.Bus(bn).theta -= sb_theta

        return IslandResult.OK, 0.0

__all__ = ['OpenDSSSolver']