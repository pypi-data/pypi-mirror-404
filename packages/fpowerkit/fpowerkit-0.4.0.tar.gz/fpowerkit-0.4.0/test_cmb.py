from fpowerkit import Grid, CombinedSolver, Estimator, Calculator, LinDistFlow2Solver, NewtonSolver

def test_cmb():
    grid = Grid.fromFile("cases/3nodes.xml")
    solver = CombinedSolver(grid=grid, estimator=Estimator.LinDistFlow2, calculator=Calculator.Newton)
    res, obj = solver.solve(0)
    print(res, obj)

def test_spl():
    grid = Grid.fromFile("cases/3nodes.xml")
    solver0 = LinDistFlow2Solver(grid=grid)
    res, obj = solver0.solve(0)
    print(res, obj)
    for b in grid.Buses:
        print(b.ID, b.V, b.theta, b.Pd, b.Qd)
    for l in grid.Lines:
        print(l.ID, l.P, l.Q, l.I)
    for g in grid.Gens:
        print(g.ID, g.P, g.Q)
    solver1 = NewtonSolver(grid=grid, is_cmb_calculator=True)
    res, obj = solver1.solve(0)
    print(res, obj)
    for b in grid.Buses:
        print(b.ID, b.V, b.theta, b.Pd, b.Qd)
    for l in grid.Lines:
        print(l.ID, l.P, l.Q, l.I)
    for g in grid.Gens:
        print(g.ID, g.P, g.Q)

if __name__ == "__main__":
    test_spl()