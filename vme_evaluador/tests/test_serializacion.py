import json

import pytest

from vme import ErrorFormato, EvaluadorVME, cargar_arbol, guardar_arbol
from vme.serializacion import arbol_desde_dict


@pytest.mark.parametrize(
    "archivo", ["thompson_simple.json", "thompson_con_estudio.json", "proveedores_costos.json"]
)
def test_ida_y_vuelta_conserva_el_arbol(ejemplos, tmp_path, archivo):
    raiz, criterio = cargar_arbol(ejemplos / archivo)
    destino = tmp_path / "copia.json"
    guardar_arbol(destino, raiz, criterio)
    assert cargar_arbol(destino) == (raiz, criterio)


def test_error_indica_la_ubicacion_del_problema():
    datos = {
        "arbol": {
            "tipo": "decision",
            "nombre": "D",
            "alternativas": [
                {"nombre": "A", "pago": 1},
                {
                    "nombre": "B",
                    "nodo": {
                        "tipo": "azar",
                        "nombre": "M",
                        "escenarios": [
                            {"nombre": "x", "probabilidad": 0.7, "pago": 1},
                            {"nombre": "y", "probabilidad": 0.7, "pago": 2},
                        ],
                    },
                },
            ],
        }
    }
    with pytest.raises(ErrorFormato, match=r"arbol\.alternativas\[1\]\.nodo: .*deben sumar 1"):
        arbol_desde_dict(datos)


@pytest.mark.parametrize(
    ("datos", "mensaje"),
    [
        ([], "objeto JSON"),
        ({"criterio": "mediana", "arbol": {}}, "Criterio desconocido"),
        ({"arbol": {"tipo": "raro", "nombre": "x"}}, "tipo de nodo"),
        ({"arbol": {"tipo": "terminal", "nombre": "x", "pago": "mucho"}}, "debe ser un número"),
        (
            {"arbol": {"tipo": "decision", "nombre": "D", "alternativas": [{"nombre": "A"}]}},
            "'nodo' o 'pago'",
        ),
    ],
)
def test_errores_de_formato(datos, mensaje):
    with pytest.raises(ErrorFormato, match=mensaje):
        arbol_desde_dict(datos)


def test_json_mal_formado(tmp_path):
    ruta = tmp_path / "malo.json"
    ruta.write_text("{ esto no es json", encoding="utf-8")
    with pytest.raises(ErrorFormato, match="JSON inválido"):
        cargar_arbol(ruta)


def test_criterio_por_defecto_es_maximizar(tmp_path):
    ruta = tmp_path / "a.json"
    ruta.write_text(
        json.dumps(
            {
                "arbol": {
                    "tipo": "decision",
                    "nombre": "D",
                    "alternativas": [{"nombre": "A", "pago": 5}, {"nombre": "B", "pago": 7}],
                }
            }
        ),
        encoding="utf-8",
    )
    raiz, criterio = cargar_arbol(ruta)
    assert EvaluadorVME(criterio).evaluar(raiz).alternativa_optima == "B"
