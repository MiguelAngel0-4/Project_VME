"""Lectura y escritura de árboles de decisión en formato JSON.

Formato (ver carpeta ``ejemplos/``)::

    {
      "criterio": "max",                  # "max" o "min"
      "arbol": {
        "tipo": "decision",
        "nombre": "¿Qué planta construir?",
        "alternativas": [
          {"nombre": "Planta grande", "costo": 0, "nodo": {
              "tipo": "azar", "nombre": "Mercado",
              "escenarios": [
                {"nombre": "Favorable",    "probabilidad": 0.5, "pago": 200000},
                {"nombre": "Desfavorable", "probabilidad": 0.5, "pago": -180000}
              ]}},
          {"nombre": "No hacer nada", "pago": 0}
        ]
      }
    }

Atajo: una alternativa o escenario puede llevar ``"pago"`` en lugar de
``"nodo"``; equivale a un nodo terminal con el mismo nombre.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .modelo import (
    Alternativa,
    Criterio,
    Escenario,
    Nodo,
    NodoAzar,
    NodoDecision,
    NodoTerminal,
)


class ErrorFormato(ValueError):
    """El contenido no describe un árbol de decisión válido."""


# --------------------------------------------------------------------------- #
# Lectura
# --------------------------------------------------------------------------- #
def cargar_arbol(ruta: str | Path) -> tuple[Nodo, Criterio]:
    try:
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ErrorFormato(f"JSON inválido en '{ruta}': {error}") from error
    return arbol_desde_dict(datos)


def arbol_desde_dict(datos: Any) -> tuple[Nodo, Criterio]:
    if not isinstance(datos, Mapping):
        raise ErrorFormato("El documento debe ser un objeto JSON con las claves 'criterio' y 'arbol'.")
    texto_criterio = datos.get("criterio", Criterio.MAXIMIZAR.value)
    try:
        criterio = Criterio(texto_criterio)
    except ValueError:
        raise ErrorFormato(f"Criterio desconocido {texto_criterio!r}; usa 'max' o 'min'.") from None
    raiz = nodo_desde_dict(_obtener(datos, "arbol", "documento"), "arbol")
    return raiz, criterio


def nodo_desde_dict(datos: Any, ruta: str = "arbol") -> Nodo:
    """Convierte un diccionario en un nodo. ``ruta`` se usa en los mensajes de error."""
    if not isinstance(datos, Mapping):
        raise ErrorFormato(f"{ruta}: se esperaba un objeto JSON.")
    tipo = _obtener(datos, "tipo", ruta)
    try:
        if tipo == "terminal":
            return NodoTerminal(_texto(datos, "nombre", ruta), _numero(datos, "pago", ruta))
        if tipo == "azar":
            escenarios = tuple(
                _escenario_desde_dict(item, f"{ruta}.escenarios[{i}]")
                for i, item in enumerate(_lista(datos, "escenarios", ruta))
            )
            return NodoAzar(_texto(datos, "nombre", ruta), escenarios)
        if tipo == "decision":
            alternativas = tuple(
                _alternativa_desde_dict(item, f"{ruta}.alternativas[{i}]")
                for i, item in enumerate(_lista(datos, "alternativas", ruta))
            )
            return NodoDecision(_texto(datos, "nombre", ruta), alternativas)
    except ErrorFormato:
        raise
    except ValueError as error:  # errores de validación del modelo
        raise ErrorFormato(f"{ruta}: {error}") from error
    raise ErrorFormato(f"{ruta}: tipo de nodo {tipo!r} desconocido (usa 'decision', 'azar' o 'terminal').")


def _escenario_desde_dict(datos: Any, ruta: str) -> Escenario:
    if not isinstance(datos, Mapping):
        raise ErrorFormato(f"{ruta}: se esperaba un objeto JSON.")
    nombre = _texto(datos, "nombre", ruta)
    return Escenario(nombre, _numero(datos, "probabilidad", ruta), _hijo_desde_dict(datos, nombre, ruta))


def _alternativa_desde_dict(datos: Any, ruta: str) -> Alternativa:
    if not isinstance(datos, Mapping):
        raise ErrorFormato(f"{ruta}: se esperaba un objeto JSON.")
    nombre = _texto(datos, "nombre", ruta)
    costo = _numero(datos, "costo", ruta) if "costo" in datos else 0.0
    return Alternativa(nombre, _hijo_desde_dict(datos, nombre, ruta), costo)


def _hijo_desde_dict(datos: Mapping[str, Any], nombre: str, ruta: str) -> Nodo:
    if "nodo" in datos:
        return nodo_desde_dict(datos["nodo"], f"{ruta}.nodo")
    if "pago" in datos:
        return NodoTerminal(nombre, _numero(datos, "pago", ruta))
    raise ErrorFormato(f"{ruta}: falta la clave 'nodo' o 'pago'.")


def _obtener(datos: Mapping[str, Any], clave: str, ruta: str) -> Any:
    if clave not in datos:
        raise ErrorFormato(f"{ruta}: falta la clave obligatoria '{clave}'.")
    return datos[clave]


def _texto(datos: Mapping[str, Any], clave: str, ruta: str) -> str:
    valor = _obtener(datos, clave, ruta)
    if not isinstance(valor, str):
        raise ErrorFormato(f"{ruta}.{clave}: debe ser texto.")
    return valor


def _numero(datos: Mapping[str, Any], clave: str, ruta: str) -> float:
    valor = _obtener(datos, clave, ruta)
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ErrorFormato(f"{ruta}.{clave}: debe ser un número.")
    return float(valor)


def _lista(datos: Mapping[str, Any], clave: str, ruta: str) -> Sequence[Any]:
    valor = _obtener(datos, clave, ruta)
    if not isinstance(valor, list):
        raise ErrorFormato(f"{ruta}.{clave}: debe ser una lista.")
    return valor


# --------------------------------------------------------------------------- #
# Escritura
# --------------------------------------------------------------------------- #
def guardar_arbol(ruta: str | Path, raiz: Nodo, criterio: Criterio) -> None:
    contenido = json.dumps(arbol_a_dict(raiz, criterio), ensure_ascii=False, indent=2)
    Path(ruta).write_text(contenido + "\n", encoding="utf-8")


def arbol_a_dict(raiz: Nodo, criterio: Criterio) -> dict[str, Any]:
    return {"criterio": criterio.value, "arbol": nodo_a_dict(raiz)}


def nodo_a_dict(nodo: Nodo) -> dict[str, Any]:
    match nodo:
        case NodoTerminal():
            return {"tipo": "terminal", "nombre": nodo.nombre, "pago": nodo.pago}
        case NodoAzar():
            return {
                "tipo": "azar",
                "nombre": nodo.nombre,
                "escenarios": [
                    {"nombre": e.nombre, "probabilidad": e.probabilidad, **_hijo_a_dict(e.nombre, e.nodo)}
                    for e in nodo.escenarios
                ],
            }
        case NodoDecision():
            return {
                "tipo": "decision",
                "nombre": nodo.nombre,
                "alternativas": [
                    {"nombre": a.nombre, "costo": a.costo, **_hijo_a_dict(a.nombre, a.nodo)}
                    for a in nodo.alternativas
                ],
            }
    raise TypeError(f"Tipo de nodo no soportado: {type(nodo).__name__}")


def _hijo_a_dict(nombre_rama: str, nodo: Nodo) -> dict[str, Any]:
    """Usa el atajo ``"pago"`` cuando el hijo es una hoja con el mismo nombre."""
    if isinstance(nodo, NodoTerminal) and nodo.nombre == nombre_rama:
        return {"pago": nodo.pago}
    return {"nodo": nodo_a_dict(nodo)}
