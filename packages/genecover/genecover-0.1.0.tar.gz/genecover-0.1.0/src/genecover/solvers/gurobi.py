import numpy as np


def covering(
    Z,
    minSize=1,
    alpha=0.05,
    weights=1.0,
    output=None,
    callBack=None,
    poolSolutions=None,
    poolSearchMode=None,
    poolGap=None,
    timeLimit=None,
    LogToConsole=1,
    restart=None,
):
    """
    Solves the minimal weight set covering problem using the Gurobi solver.

    Args:
        Z (np.ndarray): A binary matrix of shape (N, d), where N is the number of samples and d is the number of genes.
        minSize (int): The minimum number of genes to select.
        alpha (float): The minimum fraction of samples that must be covered.
        weights (np.ndarray): A 1D array of weights for each gene. Higher weights indicate higher cost for selection.
        output (int): Enables or disables solver output. Set to 1 to print optimization details, 0 to suppress.
        callBack (Callable): A callback function to be invoked during optimization.
        poolSolutions (int): Number of solutions to store in the solution pool. See: https://www.gurobi.com/documentation/current/refman/poolsolutions.html
        poolSearchMode (int): Mode for exploring the MIP search tree. See: https://www.gurobi.com/documentation/current/refman/poolsearchmode.html
        poolGap (float): Relative MIP optimality gap for accepting solutions into the pool. See:https://www.gurobi.com/documentation/current/refman/poolgap.html
        timeLimit (float): Time limit (in seconds) for the optimization run.
        LogToConsole (int): Whether to print the optimization log. Set to 1 to enable.
        restart (gurobipy.Model): A Gurobi model instance to restart the optimization from.

    Returns:
        gurobipy.Model: The solved (or solvable) Gurobi model instance.
    """
    try:
        import gurobipy as grb
    except ImportError as e:
        raise ImportError(
            "covering requires gurobipy. Install with: pip install 'genecover[gurobi]' "
            "(and ensure you have a valid Gurobi license)."
        ) from e

    Z = np.asarray(Z)

    if restart is not None:
        cov = restart
        if output is not None:
            cov.Params.OutputFlag = output
        if poolSolutions is not None:
            cov.Params.PoolSolutions = poolSolutions
        if poolSearchMode is not None:
            cov.Params.PoolSearchMode = poolSearchMode
        if poolGap is not None:
            cov.Params.PoolGap = poolGap
        if timeLimit is not None:
            cov.Params.TimeLimit = timeLimit
        if LogToConsole is not None:
            cov.Params.LogToConsole = LogToConsole
        if callBack is None:
            cov.optimize()
        else:
            cov.optimize(callBack)
        return cov

    if np.isscalar(minSize):
        minSize = [minSize]
    if np.isscalar(alpha):
        alpha = [alpha] * len(minSize)
    N = Z.shape[0]
    d = Z.shape[1]
    if type(weights) == str and weights == "prob":
        w = 1 - 0.01 * np.mean(Z, axis=0)
    elif np.isscalar(weights):
        w = weights * np.ones(d)
    else:
        w = weights

    cov = grb.Model()
    if output is not None:
        cov.Params.OutputFlag = output
    if poolSolutions is not None:
        cov.Params.PoolSolutions = poolSolutions
    if poolSearchMode is not None:
        cov.Params.PoolSearchMode = poolSearchMode
    if poolGap is not None:
        cov.Params.PoolGap = poolGap
    if timeLimit is not None:
        cov.Params.TimeLimit = timeLimit
    if LogToConsole is not None:
        cov.Params.LogToConsole = LogToConsole

    nlevels = len(minSize)
    x = []
    y = []
    for l in range(nlevels):
        x.append(cov.addMVar(d, vtype=grb.GRB.BINARY))
    for l in range(nlevels):
        y.append(cov.addMVar(N, vtype=grb.GRB.BINARY))

    for l in range(nlevels):
        expr = y[l].sum()
        cov.addConstr(expr >= N * (1 - alpha[l]), "Coverage_" + str(l))

    for l in range(nlevels):
        expr = Z @ x[l] - minSize[l] * y[l]
        cov.addConstr(expr >= 0, "covered_" + str(l))

        # if B is not None:
        #     exprB = B @ x[l] - MinMarkerPerClass
        #     cov.addConstr(exprB >= 0, 'MinMarkerPerClass_' + str(l))

    for l in range(nlevels - 1):
        for j in range(d):
            cov.addConstr(
                x[l + 1].tolist()[j] - x[l].tolist()[j] >= 0,
                name="Nesting" + str(j) + "_" + str(l),
            )

    expr = grb.LinExpr()
    for l in range(nlevels):
        expr += (w * x[l]).sum()
    cov.setObjective(expr, grb.GRB.MINIMIZE)

    if callBack is None:
        cov.optimize()
    else:
        cov.optimize(callBack)

    return cov