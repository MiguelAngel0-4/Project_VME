import pytest

from vme import Criterio, EvaluadorVME
from vme.cli import CODIGO_ERROR, CODIGO_OK, main
from vme.consola import ConstructorInteractivo, convertir_numero


def construir_con(respuestas):
    entradas = iter(respuestas)
    salidas: list[str] = []
    constructor = ConstructorInteractivo(entrada=lambda _prompt: next(entradas), salida=salidas.append)
    raiz, criterio = constructor.construir()
    return raiz, criterio, "\n".join(salidas)


def test_dialogo_completo_con_errores_de_captura():
    # fmt: off
    respuestas = [
        "9", "1",                        # opción inválida, luego maximizar
        "¿Qué planta construir?",
        "1", "3",                        # menos de 2 alternativas → reintenta
        # Alternativa 1
        "Planta grande", "", "2",
        "Mercado", "2",
        "Favorable", "abc", "0.5",       # número inválido → reintenta
        "Desfavorable", "",              # Enter = probabilidad restante (0.5)
        "1", "200000",
        "1", "-180000",
        # Alternativa 2 (nombre repetido primero)
        "Planta grande", "Planta pequeña", "", "2",
        "Mercado", "2",
        "Favorable", "70%", "Desfavorable", "0.7",   # suman 1.4 → reingresar
        "Favorable", "50%", "Desfavorable", "",
        "1", "100000",
        "1", "-20000",
        # Alternativa 3
        "No hacer nada", "", "1", "0",
    ]
    # fmt: on
    raiz, criterio, salida = construir_con(respuestas)

    assert criterio is Criterio.MAXIMIZAR
    assert "deben sumar 1" in salida
    assert "Ya existe" in salida
    resultado = EvaluadorVME(criterio).evaluar(raiz)
    assert resultado.alternativa_optima == "Planta pequeña"
    assert resultado.vme_optimo == pytest.approx(40_000)


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [("1500", 1500), ("-180000", -180000), ("0,25", 0.25), ("$ 1_000", 1000), ("30%", 0.3)],
)
def test_convertir_numero(texto, esperado):
    assert convertir_numero(texto) == pytest.approx(esperado)


@pytest.mark.parametrize("texto", ["", "abc", "inf"])
def test_convertir_numero_invalido(texto):
    with pytest.raises(ValueError):
        convertir_numero(texto)


def test_cli_con_archivo(ejemplos, capsys):
    assert main(["--archivo", str(ejemplos / "thompson_simple.json")]) == CODIGO_OK
    salida = capsys.readouterr().out
    assert "★ Planta pequeña" in salida
    assert "VME ÓPTIMO: $40,000.00" in salida


def test_cli_permite_cambiar_criterio(ejemplos, capsys):
    assert main(["-a", str(ejemplos / "thompson_simple.json"), "-c", "min"]) == CODIGO_OK
    assert "VME ÓPTIMO: $0.00" in capsys.readouterr().out


def test_cli_archivo_inexistente(tmp_path, capsys):
    assert main(["-a", str(tmp_path / "no_existe.json")]) == CODIGO_ERROR
    assert "Error" in capsys.readouterr().err
