import pytest

from vme import Alternativa, Escenario, NodoAzar, NodoDecision, NodoTerminal


def hoja(pago: float, nombre: str = "Hoja") -> NodoTerminal:
    return NodoTerminal(nombre, pago)


def test_probabilidades_que_no_suman_uno_son_rechazadas():
    with pytest.raises(ValueError, match="deben sumar 1"):
        NodoAzar("Mercado", (Escenario("A", 0.5, hoja(1)), Escenario("B", 0.4, hoja(2))))


def test_tolera_errores_de_redondeo_en_probabilidades():
    tercio = 1 / 3
    nodo = NodoAzar("Dado", tuple(Escenario(str(i), tercio, hoja(i)) for i in range(3)))
    assert len(nodo.escenarios) == 3


@pytest.mark.parametrize("probabilidad", [-0.1, 1.5, float("nan")])
def test_probabilidad_fuera_de_rango(probabilidad):
    with pytest.raises(ValueError):
        Escenario("X", probabilidad, hoja(0))


def test_nombres_repetidos_en_decision():
    with pytest.raises(ValueError, match="repetido"):
        NodoDecision("D", (Alternativa("A", hoja(1)), Alternativa("A", hoja(2))))


def test_costo_negativo_rechazado():
    with pytest.raises(ValueError, match="negativo"):
        Alternativa("A", hoja(1), costo=-5)


def test_nombre_vacio_rechazado():
    with pytest.raises(ValueError, match="nombre"):
        NodoTerminal("   ", 10)


def test_listas_se_convierten_en_tuplas_inmutables():
    nodo = NodoDecision("D", [Alternativa("A", hoja(1))])  # type: ignore[arg-type]
    assert isinstance(nodo.alternativas, tuple)
