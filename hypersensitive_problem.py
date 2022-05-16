"""Hypersensitive problem.

Example 4.4 from Betts, J. T. (2010). Practical methods for optimal control
and estimation using nonlinear programming - 2nd Edition. Society for
Industrial and Applied Mathematics, p170 - 171.

"""

import numpy as np
import sympy as sym
import matplotlib.pyplot as plt
import pycollo

for i in ['radau']:
    y, u = sym.symbols("y u")

    problem = pycollo.OptimalControlProblem(name="Hypersensitive problem")
    # problem.settings.quadrature_method = "lobatto"
    # problem.settings.quadrature_method = "gauss"
    # problem.settings.quadrature_method = "gauss differential"
    # problem.settings.quadrature_method = "radau"
    # problem.settings.quadrature_method = "radau differential"
    problem.settings.quadrature_method = i
    # problem.settings.max_mesh_iterations = 1
    phase = problem.new_phase(name="A")
    phase.state_variables = y
    phase.control_variables = u
    phase.state_equations = [-y**3 + u]
    phase.integrand_functions = [0.5*(y**2 + u**2)]
    phase.auxiliary_data = {}

    phase.bounds.initial_time = 0.0
    phase.bounds.final_time = 10000.0
    phase.bounds.state_variables = [[-50, 50]]
    phase.bounds.control_variables = [[-50, 50]]
    phase.bounds.integral_variables = [[0, 100000]]
    phase.bounds.initial_state_constraints = [[1.0, 1.0]]
    phase.bounds.final_state_constraints = [[1.5, 1.5]]

    phase.guess.time = np.array([0.0, 10000.0])
    phase.guess.state_variables = np.array([[1.0, 1.5]])
    phase.guess.control_variables = np.array([[0.0, 0.0]])
    phase.guess.integral_variables = np.array([4])

    problem.objective_function = phase.integral_variables[0]

    problem.settings.display_mesh_result_graph = True

    problem.initialise()
    problem.solve()


#     control_solution = problem.solution.control[0][0]
#     time_solution = problem.solution.tau[0]

#     index = [i for i in range(len(control_solution)) if float(control_solution[i]) == 0.0]
#     control_solution = np.delete(control_solution,index)
#     time_solution = np.delete(time_solution,index)
#     plt.plot(time_solution[1:-1], control_solution[1:-1], marker="x",label=i)
# plt.legend()
# plt.show()