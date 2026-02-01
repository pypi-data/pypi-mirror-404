from typing import Callable, Optional, Tuple, Union, List, Dict, Any
from feasytools import TimeFunc, SegFunc, ConstFunc
from xml.etree.ElementTree import Element


FloatVar = Optional[float]
NFloat = Optional[float]
FloatLike = Union[int, float, TimeFunc, List[Tuple[int, float]]]
NFloatLike = Union[None, FloatLike]
FloatVals = Union[int, float]


class Projector:
    def __init__(self, proj_param:str, offset_x:float = 0.0, offset_y:float = 0.0):
        from pyproj import Proj
        self._proj = Proj(projparams=proj_param)
        self._offset_x = offset_x
        self._offset_y = offset_y
    
    def __call__(self, v1: float, v2: float, inverse: bool = False) -> Tuple[float, float]:
        if inverse:
            return self.convXY2LL(v1, v2)
        else:
            return self.convLL2XY(v1, v2)
    
    def convLL2XY(self, lon: float, lat: float) -> Tuple[float, float]:
        x, y = self._proj(lon, lat)
        return x + self._offset_x, y + self._offset_y
    
    def convXY2LL(self, x: float, y: float) -> Tuple[float, float]:
        lon, lat = self._proj(x - self._offset_x, y - self._offset_y, inverse=True)
        return lon, lat
    
    @staticmethod
    def fromXML(node: Element):
        proj_str = node.get("projection","!")
        net_offset = tuple(map(float, node.get("netOffset", "0,0").split(",")))
        return Projector(proj_str, net_offset[0], net_offset[1])
    

class PositionBase:
    def __init__(self, x: float, y: float, proj:Optional[Projector] = None):
        self.x = x
        self.y = y
        self._proj = proj
    
    @property
    def pos(self) -> Tuple[float, float]:
        return (self.x, self.y)

    position = pos
    
    @property
    def LonLat(self) -> Tuple[float, float]:
        assert self._proj is not None, "No projector defined for this object."
        return self._proj(self.x, self.y, inverse=True)
    
    @staticmethod
    def load_pos_from_xml(node: Element, proj:Optional[Projector] = None) -> Tuple[float, float]:
        if proj is None:
            x = float(node.attrib["x"])
            y = float(node.attrib["y"])
        else:
            x = node.attrib.get("x")
            y = node.attrib.get("y")
            if x is None or y is None:
                lon = node.attrib["Lon"]
                lat = node.attrib["Lat"]
                x, y = proj(float(lon), float(lat))
            else:
                x = float(x); y = float(y)
        return x, y


class VarBank:
    def __init__(self):
        try:
            from cvxpy import Variable, Constraint
        except ImportError:
            raise ImportError("cvxpy is required for VarBank. Please install it via 'pip install cvxpy'.")
        self._vars:Dict[str, Tuple[object, str, Variable, Optional[Callable]]] = {}
        self._autocons:Dict[str, Constraint] = {}

    def __var(self, name:str, obj: object, attr: str, value = None, boolean:bool = False, integer:bool = False,
            nonneg:bool = False, lb: Optional[float] = None, ub: Optional[float] = None,
            reflect:Optional[Callable] = None):
        try:
            from cvxpy import Variable
        except ImportError:
            raise ImportError("cvxpy is required for VarBank. Please install it via 'pip install cvxpy'.")
        if name in self._vars:
            return self._vars[name][2]
        if hasattr(obj, attr):
            value = getattr(obj, attr) if value is None else value
        else:
            raise ValueError(f"Object {obj} has no attribute {attr} to initialize variable {name}")
        v = Variable(name = name, value = value, nonneg = nonneg, boolean = boolean, integer = integer)
        self._vars[name] = (obj, attr, v, reflect)
        if lb is not None and ((nonneg and lb > 0) or not nonneg):
            if name + "_lb" not in self._autocons:
                self._autocons[name + "_lb"] = (v >= lb)
        if ub is not None and ub < float('inf'):
            if nonneg and ub < 0:
                raise ValueError(f"Upper bound {ub} is less than 0 for non-negative variable {name}")
            if name + "_ub" not in self._autocons:
                self._autocons[name + "_ub"] = (v <= ub)
        return v
    @property
    def variables(self):
        '''Get all variables in the bank.'''
        return {name: var[2] for name, var in self._vars.items()}
    
    @property
    def constraints(self):
        '''Get all constraints in the bank.'''
        return self._autocons
    
    def __getitem__(self, name: str):
        '''Get a variable by name.'''
        if name in self._vars:
            return self._vars[name][2]
        else:
            raise KeyError(f"Variable {name} not found in the bank.")
    
    def fvar(self, name:str, obj: object, attr: str, value:Optional[float] = None,
            nonneg:bool = False, lb: Optional[float] = None, ub: Optional[float] = None,
            reflect:Optional[Callable[[float], float]] = None):
        '''Create a variable with the given name and attributes.'''
        return self.__var(name, obj, attr, value, False, False, nonneg, lb, ub, reflect)
    
    def ivar(self, name:str, obj: object, attr: str, value:Optional[int] = None,
            nonneg:bool = False, lb: Optional[float] = None, ub: Optional[float] = None, 
            reflect:Optional[Callable[[int], int]] = None):
        '''Create an integer variable with the given name and attributes.'''
        return self.__var(name, obj, attr, value, False, True, nonneg, lb, ub, reflect)
    
    def bvar(self, name:str, obj: object, attr: str, value:Optional[bool] = None):
        '''Create a boolean variable with the given name and attributes.'''
        return self.__var(name, obj, attr, value, True, False, False, None, None)    
    
    def apply(self):
        for obj, attr, v, ref in self._vars.values():
            if hasattr(obj, attr):
                if v.value is None:
                    setattr(obj, attr, None)
                else:
                    setattr(obj, attr, v.value if ref is None else ref(v.value))
            else:
                raise AttributeError(f"Object {obj} has no attribute {attr}")

    def __contains__(self, name: str) -> bool:
        return name in self._vars
    
def Float2Func(v: FloatLike) -> TimeFunc:
    if isinstance(v, (float, int)):
        return ConstFunc(v)
    elif isinstance(v, TimeFunc):
        return v
    else:
        return SegFunc(v)

def Func2Elem(f: TimeFunc, tag: str, mul:float = 1, unit:str = "") -> Element:
    if isinstance(f, ConstFunc):
        e = Element(tag,{
            "const": str(f(0)*mul) + unit
        })
    elif isinstance(f, SegFunc):
        e = f.toXMLNode(tag, "item", "time", "value", lambda t, v: f"{v*mul:.4f}{unit}")
    else:
        raise ValueError("Unknown function type")
    return e


def FVstr(s: FloatVar): return "<unsolved>" if s is None else str(s)

def ReadVal(s: str) -> 'tuple[float, str]':
    if s.endswith("pu"):
        return float(s[:-2]), "pu"
    elif s.endswith("kVA"):
        return float(s[:-3]), "kVA"
    elif s.endswith("kvar"):
        return float(s[:-4]), "kvar"
    elif s.endswith("kW"):
        return float(s[:-2]), "kW"
    elif s.endswith("MVA"):
        return float(s[:-3]), "MVA"
    elif s.endswith("Mvar"):
        return float(s[:-4]), "Mvar"
    elif s.endswith("MW"):
        return float(s[:-2]), "MW"
    elif s.endswith("kV"):
        return float(s[:-2]), "kV"
    elif s.endswith("V"):
        return float(s[:-1]), "V"
    elif s.endswith("kA"):
        return float(s[:-2]), "kA"
    elif s.endswith("ohm"):
        return float(s[:-3]), "ohm"
    elif s.endswith("$/puh"):
        return float(s[:-5]), "$/puh"
    elif s.endswith("$/puh2"):
        return float(s[:-6]), "$/puh2"
    elif s.endswith("$"):
        return float(s[:-1]), "$"
    elif s.endswith("$/kWh"):
        return float(s[:-5]), "$/kWh"
    elif s.endswith("$/MWh"):
        return float(s[:-5]), "$/MWh"
    elif s.endswith("$/kWh2"):
        return float(s[:-6]), "$/kWh2"
    elif s.endswith("$/MWh2"):
        return float(s[:-6]), "$/MWh2"
    elif s.endswith("kWh"):
        return float(s[:-3]), "kWh"
    elif s.endswith("MWh"):
        return float(s[:-3]), "MWh"
    elif s.endswith("kWh2"):
        return float(s[:-4]), "kWh2"
    elif s.endswith("MWh2"):
        return float(s[:-4]), "MWh2"
    else:
        return float(s), ""
    
def _valconv(v:FloatVals, u:str, sb_mva, ub_kv) -> FloatVals:
        if u == "pu":
            return v
        elif u == "kVA":
            return v / (sb_mva * 1000)
        elif u == "kvar":
            return v / (sb_mva * 1000)
        elif u == "kW":
            return v / (sb_mva * 1000)
        elif u == "MVA":
            return v / sb_mva
        elif u == "Mvar":
            return v / sb_mva
        elif u == "MW":
            return v / sb_mva
        elif u == "kV":
            return v / ub_kv
        elif u == "V":
            return v / (ub_kv * 1000)
        elif u == "kA":
            return v / (sb_mva / (ub_kv * 3 ** 0.5))
        elif u == "ohm":
            return v * ub_kv ** 2 / sb_mva
        elif u == "$/puh" or u == "$/puh2" or u == "$":
            return v
        elif u == "$/kWh":
            return v * (sb_mva * 1000)
        elif u == "$/MWh":
            return v * sb_mva
        elif u == "$/kWh2":
            return v * (sb_mva * 1000 * sb_mva * 1000)
        elif u == "$/MWh2":
            return v * (sb_mva * sb_mva)
        else:
            return v

def ReadConst(s:str, sb_mva:float, ub_kv:float) -> float:
    v, u = ReadVal(s)
    if u == "": u = "pu"
    return _valconv(v, u, sb_mva, ub_kv)

def ReadNFloatLike(e: Optional[Element], sb_mva:float, ub_kv:float) -> NFloatLike:
    if e is None: return None
    if "const" in e.attrib:
        v, u = ReadVal(e.attrib["const"])
        if u == "": u = e.attrib.get("unit","")
        return _valconv(v, u, sb_mva, ub_kv)
    else:
        repeat = int(e.attrib.get("repeat", "1"))
        period = int(e.attrib.get("period", "0"))
        sf = SegFunc()
        for itm in e:
            time = int(itm.attrib["time"])
            v, u = ReadVal(itm.attrib["value"])
            sf.add(time, _valconv(v, u, sb_mva, ub_kv))
        return sf.repeat(repeat, period)

def ReadFloatLike(e: Optional[Element], sb_mva:float, ub_kv:float) -> FloatLike:
    r = ReadNFloatLike(e, sb_mva, ub_kv)
    assert r is not None
    return r

__all__ = [
    'Projector',
    'PositionBase',
    'VarBank', 
    'Float2Func', 
    'Func2Elem', 
    'FVstr', 
    'ReadVal', 
    'ReadConst', 
    'ReadFloatLike', 
    'ReadNFloatLike', 
    'NFloat', 
    'FloatLike', 
    'NFloatLike', 
    'FloatVals', 
    'FloatVar'
]