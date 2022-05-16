import numpy as np

import pycollo


class BackendMock:
    def __init__(self, ocp):
        self.ocp = ocp


ocp = pycollo.OptimalControlProblem("Dummy OCP")
ocp.settings.quadrature_method = "gauss"
# ocp.settings.quadrature_method = "lobatto"

backend = BackendMock(ocp)
quadrature = pycollo.quadrature.Quadrature(backend)
# print(quadrature.quadrature_point(5))
# print(quadrature.quadrature_weight(5))
# print(quadrature.butcher_array(5))
print(quadrature.D_matrix(5))
print(quadrature.A_matrix(5))
# print(quadrature.A_index_array(5))
# print(quadrature.D_index_array(5))
