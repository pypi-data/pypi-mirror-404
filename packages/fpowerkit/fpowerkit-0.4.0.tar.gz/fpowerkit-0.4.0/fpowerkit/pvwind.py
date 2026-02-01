import math
from xml.etree.ElementTree import Element
from typing import Any, Optional
from .utils import *

class PVWind(PositionBase):
    '''
    Model of PV Panel and Wind Turbine
        Such generators are modeled as no operation cost.
        Active power output is a given function of time.
        Reactive power output is calculated from the power factor.
        Not all the power output is used, the maximum power abondon rate is given.
    '''
    def __init__(self, id: str, busid:str, p: FloatLike, pf: float,
            cc:float, tag: str, x:float, y:float, proj:Optional[Any] = None):
        '''
        Initialize
            id: PV Panel ID
            busid: ID of the bus where the PV panel is located
            p: Active power output, pu
            pf: Power factor, cos(phi). Reactive output Q = P * sqrt(1 - PF**2)
            cc: curtail cost, $/puh
            tag: "PV" or "Wind", indicating the type of the generator
            x: X coordinate of the PV Panel
            y: Y coordinate of the PV Panel
        '''
        super().__init__(x, y, proj)
        self._id = id
        self._bus = busid
        self._p = Float2Func(p)
        self._pf = pf
        self._cc = cc
        self._tag = tag
        self._cr:FloatVar = None
        self._pr:FloatVar = None
        self._qr:FloatVar = None
    
    @property
    def ID(self):
        '''Name of the PV Panel'''
        return self._id
    
    @property
    def BusID(self):
        '''ID of the bus where the PV panel is located'''
        return self._bus
    
    @property
    def P(self):
        '''Active power output, pu'''
        return self._p
    @P.setter
    def P(self, p: FloatLike):
        self._p = Float2Func(p)
    
    @property
    def PF(self):
        '''Power factor, cos(phi). Reactive output Q = P * tan φ'''
        return self._pf
    @PF.setter
    def PF(self, pf: float):
        self._pf = pf
    
    @property
    def tanPhi(self):
        return math.sqrt(1 - self._pf**2) / self._pf

    def Q(self, _t):
        '''Reactive power output, pu'''
        return self.P(_t) * self.tanPhi
    
    def __repr__(self) -> str:
        return (f"PVPanel(id='{self.ID}', busid='{self.BusID}', P={self.P}, PF={self.PF})")

    def __str__(self) -> str:
        return repr(self)
    
    def str_t(self, _t: int) -> str:
        return (f"PVPanel(id='{self.ID}', busid='{self.BusID}', P={self.P(_t)}, PF={self.PF})")
    
    @property
    def Tag(self) -> str:
        '''Return the type of the generator'''
        return self._tag
    @Tag.setter
    def Tag(self, tag: str):
        '''Set the type of the generator'''
        self._tag = tag
        
    @property
    def CR(self):
        '''Curtailment rate'''
        return self._cr
    
    @property
    def CC(self):
        '''Curtailment cost, $/puh'''
        return self._cc
    @CC.setter
    def CC(self, cc: float):
        '''Set the curtailment cost, $/puh'''
        self._cc = cc

    def Pr_var(self, bank: VarBank, t:int = 0):
        '''Return a variable for the real power output'''
        return bank.fvar(f"{self.ID}_Pr", self, "_pr", value=self.P(t), nonneg=True, ub = self.P(t))
    
    def Qr_var(self, bank: VarBank, t:int = 0):
        '''Return a variable for the reactive power output'''
        vp = self.Pr_var(bank, t)
        vq = bank.fvar(f"{self.ID}_Qr", self, "_qr")
        cons_name = f"{self.ID}_pf"
        if cons_name not in bank._autocons:
            bank._autocons[cons_name] = (vq == vp * self.tanPhi)

    @property
    def Pr(self):
        '''Real power output'''
        return self._pr
    
    @property
    def Qr(self):
        '''Reactive power output'''
        return self._qr
    
    @staticmethod
    def fromXML(node: Element, Sb_MVA: float, Ub_kV: float, proj:Optional[Any] = None) -> 'PVWind':
        '''
        Load PV Panel from XML node
            node: XML node
        '''
        id = node.attrib["ID"]
        busid = node.attrib["Bus"]
        p = ReadFloatLike(node.find("P"), Sb_MVA, Ub_kV)
        pf = float(node.attrib["pf"])
        cc = ReadConst(node.attrib["cc"], Sb_MVA, Ub_kV) if "cc" in node.attrib else 0
        tag = node.tag
        x, y = PositionBase.load_pos_from_xml(node, proj)
        return PVWind(id, busid, p, pf, cc, tag, x, y, proj)

    def toXMLNode(self, Sb_MVA:Optional[float] = None, Sb_kVA:Optional[float] = None) -> 'Element':
        '''Convert to XML node'''
        e = Element(self._tag, {
            "ID": self.ID,
            "Bus": self.BusID,
            "pf": str(self.PF),
            "x": f"{self.x:.6f}",
            "y": f"{self.y:.6f}"
        })
        if Sb_MVA is not None and Sb_kVA is not None:
            raise ValueError("Provide only ONE of Sb_MVA or Sb_kVA.")
        if Sb_MVA is not None:
            mul = Sb_MVA
            unit = ["MW", "$/MWh"]
        elif Sb_kVA is not None:
            mul = Sb_kVA
            unit = ["kW", "$/kWh"]
        else:
            mul = 1
            unit = ["pu", "$/puh"]
        e.append(Func2Elem(self.P, "P", mul, unit[0]))
        e.attrib["cc"] = str(self.CC*mul) + unit[1]
        
        return e

__all__ = ['PVWind']