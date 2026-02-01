import math
from typing import Optional
from xml.etree.ElementTree import Element
from .utils import *


class Line:
    R: float  # pu
    X: float  # pu
    P: FloatVar  # pu
    Q: FloatVar  # pu
    I: FloatVar  # pu

    def __init__(self, id: str, fbus: str, tbus: str, r_pu: float, x_pu: float, i_pu: NFloat = None, 
            p_pu: NFloat = None, q_pu: NFloat = None, max_I_kA: float = math.inf, length_km: NFloat = None, active: bool = True):
        '''
        Initialize
            id: Line ID
            fbus: ID of start bus
            tbus: ID of end bus
            r_pu: Resistance, pu
            x_pu: Reactance, pu
        '''
        self._id = id
        self._fBus = fbus
        self._tBus = tbus
        self.R = r_pu
        self.X = x_pu
        self.I = i_pu
        self._max_I = max_I_kA
        self.P = p_pu
        self.Q = q_pu
        self.L = length_km
        self.active = active

    def active_var(self, bank: VarBank):
        '''Return a variable indicating whether the line is active'''
        return bank.bvar(f"{self.ID}_active", self, "active", value=self.active)
    
    def I_var(self, bank: VarBank):
        '''Return a variable for the current of the line'''
        return bank.fvar(f"{self.ID}_I", self, "I", value=self.I, nonneg=True, lb=0.0, ub=self.max_I)
    
    def I2_var(self, bank: VarBank):
        '''Return a variable for the square of the current of the line'''
        i = self.I if self.I is not None else 0.0
        return bank.fvar(f"{self.ID}_I2", self, "I", value=i**2, nonneg=True, 
                         lb=0.0, ub=self.max_I**2, reflect=lambda x: math.sqrt(x))
    
    def P_var(self, bank: VarBank):
        '''Return a variable for the real power flow of the line'''
        return bank.fvar(f"{self.ID}_P", self, "P", value=self.P)
    
    def Q_var(self, bank: VarBank):
        '''Return a variable for the reactive power flow of the line'''
        return bank.fvar(f"{self.ID}_Q", self, "Q", value=self.Q)
    
    @property
    def ID(self) -> str:
        '''Name of the line'''
        return self._id
    
    @property
    def fBus(self) -> str:
        '''ID of the start bus'''
        return self._fBus
    
    @property
    def tBus(self) -> str:
        '''ID of the end bus'''
        return self._tBus
    
    @property
    def pair(self):
        '''Syntax candy of (self.fBus, self.tBus)'''
        return (self.fBus, self.tBus)

    @property
    def max_I(self):
        '''Maximum current, kA'''
        return self._max_I
    @max_I.setter
    def max_I(self, max_I_kA: float):
        assert max_I_kA >= 0, "max_I should be non-negative"
        self._max_I = max_I_kA
    
    @property
    def Z(self) -> complex:
        '''Impedance of the line, pu'''
        return self.R + 1j * self.X
    
    def __repr__(self) -> str:
        return (f"Line(id='{self.ID}', fbus='{self.fBus}', tbus='{self.tBus}', r_pu={self.R}, " + 
                f"x_pu={self.X}, i_pu={self.I}, p_pu={self.P}, q_pu={self.Q})")

    def __str__(self) -> str:
        return repr(self)
    
    def str_t(self, _t: int, /) -> str:
        return self.__str__()

    @staticmethod
    def fromXML(node: 'Element', Zb_Ohm: float):
        id = node.attrib["ID"]
        f = node.attrib["From"]
        t = node.attrib["To"]
        r, ru = ReadVal(node.attrib["R"])
        if ru.lower() == "ohm": r = float(r) / Zb_Ohm
        elif ru.lower() in ["pu",""]: r = float(r)
        else: raise ValueError(f"Unknown unit '{ru}' for R, only 'ohm','pu', and non-unit (treated as pu) are supported")
        x, xu = ReadVal(node.attrib["X"])
        if xu.lower() == "ohm": x = float(x) / Zb_Ohm
        elif xu.lower() in ["pu",""]: x = float(x)
        else: raise ValueError(f"Unknown unit '{xu}' for X, only 'ohm','pu', and non-unit (treated as pu) are supported")
        max_I = float(node.attrib.get("MaxIkA", math.inf))
        l = float(node.attrib.get("Length_km", -1))
        return Line(id, f, t, r, x, max_I_kA=max_I, length_km=l)
    
    def toXMLNode(self, Zb_Ohm: Optional[float] = None) -> 'Element':
        return Element("line", {
            "ID": self.ID,
            "From": self.fBus,
            "To": self.tBus,
            "R": f"{self.R*Zb_Ohm:.6f}ohm" if Zb_Ohm is not None else f"{self.R:.8f}pu",
            "X": f"{self.X*Zb_Ohm:.6f}ohm" if Zb_Ohm is not None else f"{self.X:.8f}pu",
            "MaxIkA": str(self.max_I),
            "Length_km": str(self.L) if self.L is not None else "-1"
        })

__all__ = ['Line']