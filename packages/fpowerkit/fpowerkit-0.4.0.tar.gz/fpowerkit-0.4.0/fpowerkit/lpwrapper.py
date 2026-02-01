from dataclasses import dataclass
from itertools import chain
from typing import Dict, Iterable, List, Optional, Union


@dataclass
class _LPVar:
    name:str
    idx:int
    lb:Optional[float] = 0
    ub:Optional[float] = None
    x:Optional[float] = None  # Solution value

    def __add__(self, other):
        expr = _LPExpr()
        expr.terms[self.idx] = 1.0
        if isinstance(other, _LPExpr):
            return expr + other
        elif isinstance(other, _LPVar):
            expr.terms[other.idx] = expr.terms.get(other.idx, 0) + 1.0
            return expr
        elif isinstance(other, (int, float)):
            expr.const = other
            return expr
        else:
            raise TypeError("Unsupported type for addition")
    
    def __sub__(self, other):
        expr = _LPExpr()
        expr.terms[self.idx] = 1.0
        if isinstance(other, _LPExpr):
            return expr - other
        elif isinstance(other, _LPVar):
            expr.terms[other.idx] = expr.terms.get(other.idx, 0) - 1.0
            return expr
        elif isinstance(other, (int, float)):
            expr.const = -other
            return expr
        else:
            raise TypeError("Unsupported type for subtraction")
    
    def __neg__(self):
        expr = _LPExpr()
        expr.terms[self.idx] = -1.0
        return expr
    
    def __mul__(self, scalar:Union[float, int]):
        expr = _LPExpr()
        expr.terms[self.idx] = scalar
        return expr
    
    def __rmul__(self, scalar:Union[float, int]):
        return self.__mul__(scalar)
    
    def __truediv__(self, scalar:Union[float, int]):
        expr = _LPExpr()
        expr.terms[self.idx] = 1.0 / scalar
        return expr

    def __le__(self, other):
        expr = _LPExpr()
        expr.terms[self.idx] = 1.0
        if isinstance(other, _LPExpr):
            return expr <= other
        elif isinstance(other, _LPVar):
            expr.terms[other.idx] = expr.terms.get(other.idx, 0) - 1.0
            return expr <= 0
        elif isinstance(other, (int, float)):
            expr.const = -other
            return expr <= 0
        else:
            raise TypeError("Unsupported type for comparison")
    
    def __ge__(self, other):
        expr = _LPExpr()
        expr.terms[self.idx] = 1.0
        if isinstance(other, _LPExpr):
            return expr >= other
        elif isinstance(other, _LPVar):
            expr.terms[other.idx] = expr.terms.get(other.idx, 0) - 1.0
            return expr >= 0
        elif isinstance(other, (int, float)):
            expr.const = -other
            return expr >= 0
        else:
            raise TypeError("Unsupported type for comparison")

class _LPEqCons:
    def __init__(self, expr:'_LPExpr'):
        self.expr = expr
        self.rhs = -expr.const
        self.expr.const = 0
    
    def __str__(self):
        return f"{str(self.expr)} == {self.rhs}"

class _LPIneqCons:
    def __init__(self, expr:'_LPExpr'):
        self.expr = expr
        self.rhs = -expr.const
        self.expr.const = 0
    
    def __str__ (self):
        return f"{str(self.expr)} <= {self.rhs}"

class _LPExpr:
    def __init__(self, terms:Optional[Dict[int, float]] = None, const:float = 0.0):
        self.terms:Dict[int, float] = terms.copy() if terms is not None else {}
        self.const = const
    
    def add_term(self, var_idx:int, coeff:float):
        if var_idx in self.terms:
            self.terms[var_idx] += coeff
        else:
            self.terms[var_idx] = coeff
    
    def add_const(self, value:float):
        self.const += value
    
    def __add__(self, other):
        if isinstance(other, _LPExpr):
            result_terms = self.terms.copy()
            for var_idx, coeff in other.terms.items():
                if var_idx in result_terms:
                    result_terms[var_idx] += coeff
                else:
                    result_terms[var_idx] = coeff
            return _LPExpr(result_terms, self.const + other.const)
        elif isinstance(other, _LPVar):
            result_terms = self.terms.copy()
            result_terms[other.idx] = result_terms.get(other.idx, 0) + 1.0
            return _LPExpr(result_terms, self.const)
        elif isinstance(other, (int, float)):
            return _LPExpr(self.terms.copy(), self.const + other)
        else:
            raise TypeError(f"Unsupported type for addition: {type(other)}")
    
    def __radd__(self, other):
        return self.__add__(other)
        
    def __sub__(self, other):
        if isinstance(other, _LPExpr):
            result_terms = self.terms.copy()
            for var_idx, coeff in other.terms.items():
                if var_idx in result_terms:
                    result_terms[var_idx] -= coeff
                else:
                    result_terms[var_idx] = -coeff
            return _LPExpr(result_terms, self.const - other.const)
        elif isinstance(other, _LPVar):
            result_terms = self.terms.copy()
            result_terms[other.idx] = result_terms.get(other.idx, 0) - 1.0
            return _LPExpr(result_terms, self.const)
        elif isinstance(other, (int, float)):
            return _LPExpr(self.terms.copy(), self.const - other)
        else:
            raise TypeError(f"Unsupported type for subtraction: {type(other)}")
    
    def __rsub__(self, other):
        if isinstance(other, _LPExpr):
            return other - self
        elif isinstance(other, _LPVar):
            return _LPExpr({other.idx: 1.0}, 0) - self
        elif isinstance(other, (int, float)):
            return _LPExpr({}, other) - self
        else:
            raise TypeError(f"Unsupported type for subtraction: {type(other)}")
    
    def __neg__(self):
        result_terms = {}
        for var_idx, coeff in self.terms.items():
            result_terms[var_idx] = -coeff
        return _LPExpr(result_terms, -self.const)
    
    def __mul__(self, scalar:Union[float, int]):
        if scalar == 0:
            return _LPExpr()
        result_terms = {}
        for var_idx, coeff in self.terms.items():
            result_terms[var_idx] = coeff * scalar
        return _LPExpr(result_terms, self.const * scalar)
    
    def __rmul__(self, scalar:Union[float, int]):
        return self.__mul__(scalar)
    
    def __truediv__(self, scalar:Union[float, int]):
        result_terms = {}
        for var_idx, coeff in self.terms.items():
            result_terms[var_idx] = coeff / scalar
        return _LPExpr(result_terms, self.const / scalar)
    
    def __eq__(self, other):
        return _LPEqCons(self - other)
    
    def __le__(self, other):
        return _LPIneqCons(self - other)
    
    def __ge__(self, other):
        return _LPIneqCons(other - self)
    
    def __str__(self):
        terms_str = [f"{coeff}*x{var_idx}" for var_idx, coeff in self.terms.items()]
        if self.const != 0:
            terms_str.append(f"{self.const}")
        return " + ".join(terms_str) if terms_str else "0"
    
    def to_string(self, prob:'LinProgProblem') -> str:
        terms_str = [f"{coeff}*{prob.get_var_name(var_idx)}" for var_idx, coeff in self.terms.items()]
        if self.const != 0:
            terms_str.append(f"{self.const}")
        return " + ".join(terms_str) if terms_str else "0"
    
    def value(self, prob:'LinProgProblem') -> float:
        val = self.const
        for var_idx, coeff in self.terms.items():
            var = prob.variables[var_idx]
            if var.x is None:
                raise ValueError(f"Variable {var.name} has no assigned value")
            val += coeff * var.x
        return val
    
    def copy(self):
        """Shallow copy of the expression."""
        return _LPExpr(self.terms.copy(), self.const)


def quicksum(items:Iterable[Union[_LPVar, _LPExpr]]) -> _LPExpr:
    result_terms = {}
    result_const = 0.0
    
    for other in items:
        if isinstance(other, _LPExpr):
            for var_idx, coeff in other.terms.items():
                if var_idx in result_terms:
                    result_terms[var_idx] += coeff
                else:
                    result_terms[var_idx] = coeff
            result_const += other.const
        elif isinstance(other, _LPVar):
            result_terms[other.idx] = result_terms.get(other.idx, 0) + 1.0
        elif isinstance(other, (int, float)):
            result_const += other
        else:
            raise TypeError(f"Unsupported type for addition: {type(other)}")
    
    return _LPExpr(result_terms, result_const)


class LinProgProblem:
    def __init__(self):
        self.__vars:List[_LPVar] = []
        self.__eqs:List[_LPEqCons] = []
        self.__ineqs:List[_LPIneqCons] = []
        self.objective:_LPExpr = _LPExpr()
    
    @property
    def variables(self) -> List[_LPVar]:
        return self.__vars
    
    @property
    def equations(self) -> List[_LPEqCons]:
        return self.__eqs
    
    @property
    def inequalities(self) -> List[_LPIneqCons]:
        return self.__ineqs
    
    @property
    def constraints(self) -> chain[Union[_LPEqCons, _LPIneqCons]]:
        return chain(self.__eqs, self.__ineqs)
    
    def get_var_name(self, idx:int) -> str:
        """
        Get the name of a variable by its index.
            idx: Index of the variable
        Returns: Name of the variable
        """
        return self.__vars[idx].name
    
    def add_var(self, name:str, lb:Optional[float] = 0, ub: Optional[float] = None):
        """
            Add a variable to the linear programming problem.
            name: Name of the variable
            lb: Lower bound of the variable
            ub: Upper bound of the variable
        """
        idx = len(self.__vars)
        v = _LPVar(name, idx, lb, ub)
        self.__vars.append(v)
        return v
    
    def add_cons(self, cons:Union[_LPEqCons, _LPIneqCons, bool]):
        """
        Add a constraint to the linear programming problem.
            cons: The constraint to add (either equality or inequality)
        """
        if isinstance(cons, _LPEqCons):
            self.__eqs.append(cons)
        elif isinstance(cons, _LPIneqCons):
            self.__ineqs.append(cons)
        elif isinstance(cons, bool):
            if not cons:
                raise ValueError("Infeasible constraint (False) added to the problem")
        else:
            raise TypeError("Unsupported constraint type")
    
    def set_objective(self, expr:Union[int, float, _LPExpr, _LPVar]):
        """设置目标函数"""
        if isinstance(expr, (int, float)):
            self.objective = _LPExpr({}, expr)
        elif isinstance(expr, _LPVar):
            self.objective = _LPExpr({expr.idx: 1.0}, 0)
        else:
            self.objective = expr

    def solve(self, minimize:bool = True):
        """
        Solve the linear programming problem.
            minimize: If True, minimize the objective; if False, maximize it.
        Returns: (status_code:int, objective_value:float)
            status_code: 0 if successful, non-zero otherwise.
            objective_value: The optimal objective value if successful, 0.0 otherwise.
        """
        obj = self.objective
        if not minimize:
            obj = -obj
        try:
            from scipy.optimize import linprog
            import numpy as np
        except Exception as e:
            raise RuntimeError("scipy.optimize.linprog is required") from e

        # objective coefficients
        n = len(self.__vars)
        c = np.zeros(n)
        for var_idx, coeff in obj.terms.items():
            c[var_idx] = coeff

        # variable bounds (None means unbounded for linprog)
        bounds = [(v.lb, v.ub) for v in self.__vars]

        # equality constraints
        m1 = len(self.__eqs)
        if m1 > 0:
            A_eq = np.zeros((m1, n))
            b_eq = np.zeros(m1)
            for i, eq in enumerate(self.__eqs):
                for var_idx, coeff in eq.expr.terms.items():
                    A_eq[i, var_idx] = coeff
                b_eq[i] = eq.rhs
        else:
            A_eq = None
            b_eq = None

        # inequality constraints (A_ub x <= b_ub)
        m2 = len(self.__ineqs)
        if m2 > 0:
            A_ub = np.zeros((m2, n))
            b_ub = np.zeros(m2)
            for i, ineq in enumerate(self.__ineqs):
                for var_idx, coeff in ineq.expr.terms.items():
                    A_ub[i, var_idx] = coeff
                b_ub[i] = ineq.rhs
        else:
            A_ub = None
            b_ub = None

        res = linprog(c=c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

        if not res.success:
            return res.status, 0.0
        
        for i, v in enumerate(self.__vars):
            v.x = res.x[i]
            
        return res.status, float(res.fun) + obj.const