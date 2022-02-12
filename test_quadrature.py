"""Test for correct numerical calculation of quadrature.

Quadrature schemes computed are: Radau (LGR), Lobatto (LGL) and Gauss (LG). 

"""


import numpy as np
import pytest
import pycollo


class BackendMock:
    def __init__(self, ocp):
        self.ocp = ocp

@pytest.fixture
def lobatto_quadrature_fixture():
    ocp = pycollo.OptimalControlProblem("Dummy OCP")
    ocp.settings.quadrature_method = "lobatto"
    backend = BackendMock(ocp)
    quadrature = pycollo.quadrature.Quadrature(backend)
    return quadrature


@pytest.fixture
def radau_quadrature_fixture():
    ocp = pycollo.OptimalControlProblem("Dummy OCP")
    ocp.settings.quadrature_method = "radau"
    backend = BackendMock(ocp)
    quadrature = pycollo.quadrature.Quadrature(backend)
    return quadrature


def test_lobatto_backend_name(lobatto_quadrature_fixture):
    quadrature = lobatto_quadrature_fixture
    assert quadrature.settings.quadrature_method == "lobatto"


def test_radau_backend_name(radau_quadrature_fixture):
    quadrature = radau_quadrature_fixture
    assert quadrature.settings.quadrature_method == "radau"


def test_lobatto_weights(lobatto_quadrature_fixture):
    quadrature = lobatto_quadrature_fixture
    weights_2 = np.array([0.5, 0.5])
    weights_3 = np.array([0.16666666666666666,
                          0.66666666666666666,
                          0.16666666666666666])
    np.testing.assert_array_equal(quadrature.quadrature_weight(2), weights_2)
    np.testing.assert_array_equal(quadrature.quadrature_weight(3), weights_3)

def test_radau_weights(radau_quadrature_fixture):
    quadrature = radau_quadrature_fixture
    weights_3 = np.round(np.array([0.500000000000000,1.50000000000000,0.0])/2,3)
    weights_4 = np.round(np.array([0.222222222222222,1.02497165237684,0.752806125400934,0.0])/2,3)
    weights_8 = np.round(np.array([0.0408163265306122,0.239227489225312,0.380949873644231,0.447109829014567,0.424703779005956,0.318204231467302,0.148988471112020,0.0])/2,3)
    np.testing.assert_array_equal(np.round(quadrature.quadrature_weight(3),3), weights_3)
    np.testing.assert_array_equal(np.round(quadrature.quadrature_weight(4),3), weights_4)
    np.testing.assert_array_equal(np.round(quadrature.quadrature_weight(8),3), weights_8)

def test_radau_points(radau_quadrature_fixture):
    quadrature = radau_quadrature_fixture
    points_3 = np.round(np.array([-1,0.333333333333333,1]),3)
    points_4 = np.round(np.array([-1,-0.289897948556636,0.689897948556636,1]),3)
    points_8 = np.round(np.array([-1,-0.853891342639482,-0.538467724060109,-0.117343037543100,0.326030619437691,0.703842800663031,0.941367145680430,1]),3)
    np.testing.assert_array_equal(np.round(quadrature.quadrature_point(3),3), points_3)
    np.testing.assert_array_equal(np.round(quadrature.quadrature_point(4),3), points_4)
    np.testing.assert_array_equal(np.round(quadrature.quadrature_point(8),3), points_8)


