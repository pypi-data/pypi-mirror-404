from enum import Enum
from typing import Tuple, Union, Iterable
from warnings import warn
from .grid import Grid
from .solbase import *

class Estimator(Enum):
    DistFlow = 'DistFlow'
    LinDistFlow = 'LinDistFlow'
    LinDistFlow2 = 'LinDistFlow2'

class Calculator(Enum):
    OpenDSS = 'OpenDSS'
    Newton = 'Newton'
    NoneSolver = 'None'

CALCULATORS_NEED_SOURCE_BUS = [Calculator.OpenDSS]

class CombinedSolver(SolverBase):
    """
    A class that use DistFlowSolver to estimate the power flow and then use OpenDSSSolver or NewtonSolver to solve the power flow problem.
    """
    def __init__(self, grid:Grid, eps:float = 1e-6, max_iter:int = 1000, *, mlrp:float = 0.5, 
            default_saveto:str = DEFAULT_SAVETO, estimator:Union[Estimator, SolverBase] = Estimator.DistFlow, 
            calculator:Calculator = Calculator.Newton, source_bus:'Union[str,Iterable[str]]' = ""):
        super().__init__(grid, eps, max_iter, default_saveto = default_saveto)

        if isinstance(estimator, Estimator):
            if estimator == Estimator.DistFlow:
                from .soldist import DistFlowSolver
                estimator = DistFlowSolver(grid, mlrp = mlrp, default_saveto=default_saveto)
            elif estimator == Estimator.LinDistFlow:
                from .solldf import LinDistFlowSolver
                estimator = LinDistFlowSolver(grid, default_saveto=default_saveto)
            elif estimator == Estimator.LinDistFlow2:
                from .solldf2 import LinDistFlow2Solver
                estimator = LinDistFlow2Solver(grid, default_saveto=default_saveto)
            else:
                raise ValueError(f"Invalid estimator type '{estimator}'. Candidates are: {list(Estimator)}")
        
        self.est = estimator
        self.cal_str = calculator
        if calculator in CALCULATORS_NEED_SOURCE_BUS:
            assert source_bus != "", "source_bus cannot be empty when using OpenDSSSolver."
            self.source_bus = source_bus
        else:
            if source_bus != "":
                warn(Warning("source_bus is ignored when not using OpenDSSSolver."))

    def solve(self, _t:int, /, *, timeout_s: float = 1) -> Tuple[GridSolveResult, float]:
        res, obj = self.est.solve(_t, timeout_s=timeout_s)
        if res == GridSolveResult.Failed:
            return res, obj
        if self.cal_str == Calculator.NoneSolver:
            return res, obj
        elif self.cal_str == Calculator.OpenDSS:
            from .soldss import OpenDSSSolver
            solver = OpenDSSSolver(self.est.grid, source_bus = self.source_bus, default_saveto=self.saveto)
        elif self.cal_str == Calculator.Newton:
            from .solnt import NewtonSolver
            solver = NewtonSolver(self.est.grid, default_saveto=self.saveto, is_cmb_calculator=True)
        else:
            raise ValueError(f"Invalid solver type '{self.cal_str}'.")
        res, obj = solver.solve(_t, timeout_s = timeout_s)
        return res, obj

    def solve_island(self, i:int, island, _t:int):
        '''Solve the island'''
        raise NotImplementedError
    
    def SetErrorSaveTo(self, path:str = DEFAULT_SAVETO):
        self.est.SetErrorSaveTo(path)
        self.saveto = path

__all__ = ["CombinedSolver", "Estimator", "Calculator", "CALCULATORS_NEED_SOURCE_BUS"]