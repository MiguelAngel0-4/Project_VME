import pytest

from vme import (
    Alternativa,
    Criterio,
    Escenario,
    EvaluadorVME,
    NodoAzar,
    NodoDecision,
    NodoTerminal,
    cargar_arbol,
)


def mercado(favorable: float, desfavorable: float, p: float = 0.5) -> NodoAzar:
    return NodoAzar(
        "Mercado",
        (
            Escenario("Favorable", p, NodoTerminal("Favorable", favorable)),
            Escenario("Desfavorable", 1 - p, NodoTerminal("Desfavorable", desfavorable)),
        ),
    )


def test_thompson_simple_elige_planta_pequena(ejemplos):
    raiz, criterio = cargar_arbol(ejemplos / "thompson_simple.json")
    resultado = EvaluadorVME(criterio).evaluar(raiz)

    valores = {rama.etiqueta: rama.valor for rama in resultado.arbol.ramas}
    assert valores == pytest.approx({"Planta grande": 10_000, "Planta pequeña": 40_000, "No hacer nada": 0})
    assert resultado.alternativa_optima == "Planta pequeña"
    assert resultado.vme_optimo == pytest.approx(40_000)


def test_thompson_con_estudio_coincide_con_el_libro(ejemplos):
    raiz, criterio = cargar_arbol(ejemplos / "thompson_con_estudio.json")
    resultado = EvaluadorVME(criterio).evaluar(raiz)

    assert resultado.vme_optimo == pytest.approx(49_200)
    decisiones = [(r.nodo, r.alternativa) for r in resultado.estrategia]
    assert decisiones == [
        ("¿Realizar estudio de mercado?", "Realizar estudio"),
        ("Planta tras estudio positivo", "Planta grande"),
        ("Planta tras estudio negativo", "Planta pequeña"),
    ]
    assert resultado.estrategia[1].contexto == ("Resultado del estudio = Positivo",)


def test_minimizacion_de_costos(ejemplos):
    raiz, criterio = cargar_arbol(ejemplos / "proveedores_costos.json")
    resultado = EvaluadorVME(criterio).evaluar(raiz)

    assert criterio is Criterio.MINIMIZAR
    assert resultado.alternativa_optima == "Proveedor B (tarifa variable)"
    assert resultado.vme_optimo == pytest.approx(11_600)
    # El costo del contrato se SUMA al minimizar: 9 800 + 3 000
    valor_c = next(r.valor for r in resultado.arbol.ramas if r.etiqueta.startswith("Proveedor C"))
    assert valor_c == pytest.approx(12_800)


def test_costo_de_alternativa_se_resta_al_maximizar():
    raiz = NodoDecision(
        "D",
        (
            Alternativa("Con inversión", NodoTerminal("x", 100), costo=30),
            Alternativa("Sin inversión", NodoTerminal("y", 60)),
        ),
    )
    resultado = EvaluadorVME().evaluar(raiz)
    assert resultado.alternativa_optima == "Con inversión"
    assert resultado.vme_optimo == pytest.approx(70)


def test_empates_se_reportan():
    raiz = NodoDecision(
        "D",
        (Alternativa("A", mercado(100, 0)), Alternativa("B", NodoTerminal("B", 50))),
    )
    resultado = EvaluadorVME().evaluar(raiz)
    assert [r.es_optima for r in resultado.arbol.ramas] == [True, True]
    assert resultado.estrategia[0].empates == ("B",)


def test_mismo_arbol_distinto_criterio():
    raiz = NodoDecision(
        "D", (Alternativa("Riesgosa", mercado(1000, -500)), Alternativa("Segura", NodoTerminal("S", 100)))
    )
    assert EvaluadorVME(Criterio.MAXIMIZAR).evaluar(raiz).alternativa_optima == "Riesgosa"
    assert EvaluadorVME(Criterio.MINIMIZAR).evaluar(raiz).alternativa_optima == "Segura"


def test_raiz_de_azar_no_tiene_alternativa_optima_en_raiz():
    resultado = EvaluadorVME().evaluar(mercado(10, 20))
    assert resultado.vme_optimo == pytest.approx(15)
    assert resultado.alternativa_optima is None
