"""Modelo de dominio de un árbol de decisión.

Tipos de nodo:

* ``NodoDecision`` (□): el decisor elige UNA de varias alternativas.
* ``NodoAzar``     (○): la naturaleza "elige" un escenario según su probabilidad.
* ``NodoTerminal`` (◁): resultado monetario final de una ruta.

Todas las clases son inmutables (``frozen``) y validan sus datos al crearse,
de modo que un árbol construido es siempre un árbol válido.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

TOLERANCIA_PROBABILIDAD = 1e-6
"""Margen permitido para que las probabilidades de un nodo de azar sumen 1."""


class Criterio(str, Enum):
    """Criterio de optimización con el que se evalúa el árbol."""

    MAXIMIZAR = "max"
    MINIMIZAR = "min"

    @property
    def descripcion(self) -> str:
        return "maximizar beneficio" if self is Criterio.MAXIMIZAR else "minimizar costo"


@dataclass(frozen=True)
class NodoTerminal:
    """Hoja del árbol: pago (beneficio o costo) al final de una ruta."""

    nombre: str
    pago: float

    def __post_init__(self) -> None:
        _validar_nombre(self.nombre)
        _validar_finito(self.pago, f"El pago de '{self.nombre}'")


@dataclass(frozen=True)
class Escenario:
    """Rama de un nodo de azar: un estado de la naturaleza y su probabilidad."""

    nombre: str
    probabilidad: float
    nodo: Nodo

    def __post_init__(self) -> None:
        _validar_nombre(self.nombre)
        _validar_finito(self.probabilidad, f"La probabilidad de '{self.nombre}'")
        if not 0.0 <= self.probabilidad <= 1.0:
            raise ValueError(
                f"La probabilidad del escenario '{self.nombre}' debe estar entre 0 y 1 "
                f"(se recibió {self.probabilidad})."
            )


@dataclass(frozen=True)
class NodoAzar:
    """Evento incierto con dos o más escenarios cuyas probabilidades suman 1."""

    nombre: str
    escenarios: tuple[Escenario, ...]

    def __post_init__(self) -> None:
        _validar_nombre(self.nombre)
        object.__setattr__(self, "escenarios", tuple(self.escenarios))
        if not self.escenarios:
            raise ValueError(f"El nodo de azar '{self.nombre}' necesita al menos un escenario.")
        _validar_nombres_unicos((e.nombre for e in self.escenarios), f"el nodo de azar '{self.nombre}'")
        total = math.fsum(e.probabilidad for e in self.escenarios)
        if not math.isclose(total, 1.0, abs_tol=TOLERANCIA_PROBABILIDAD):
            raise ValueError(
                f"Las probabilidades del nodo de azar '{self.nombre}' suman {total:.6g}, pero deben sumar 1."
            )


@dataclass(frozen=True)
class Alternativa:
    """Rama de un nodo de decisión.

    ``costo`` es un desembolso fijo por elegir la alternativa (p. ej. una
    inversión o el precio de un estudio). Al maximizar se RESTA del VME y al
    minimizar se SUMA, porque en ambos casos empeora el resultado.
    """

    nombre: str
    nodo: Nodo
    costo: float = 0.0

    def __post_init__(self) -> None:
        _validar_nombre(self.nombre)
        _validar_finito(self.costo, f"El costo de '{self.nombre}'")
        if self.costo < 0:
            raise ValueError(f"El costo de la alternativa '{self.nombre}' no puede ser negativo.")


@dataclass(frozen=True)
class NodoDecision:
    """Punto donde el decisor debe elegir entre varias alternativas."""

    nombre: str
    alternativas: tuple[Alternativa, ...]

    def __post_init__(self) -> None:
        _validar_nombre(self.nombre)
        object.__setattr__(self, "alternativas", tuple(self.alternativas))
        if not self.alternativas:
            raise ValueError(f"El nodo de decisión '{self.nombre}' necesita al menos una alternativa.")
        _validar_nombres_unicos((a.nombre for a in self.alternativas), f"el nodo de decisión '{self.nombre}'")


Nodo: TypeAlias = NodoTerminal | NodoAzar | NodoDecision


# --------------------------------------------------------------------------- #
# Validaciones auxiliares
# --------------------------------------------------------------------------- #
def _validar_nombre(nombre: str) -> None:
    if not isinstance(nombre, str) or not nombre.strip():
        raise ValueError("Todo nodo, escenario y alternativa necesita un nombre no vacío.")


def _validar_finito(valor: float, descripcion: str) -> None:
    if not math.isfinite(valor):
        raise ValueError(f"{descripcion} debe ser un número finito (se recibió {valor}).")


def _validar_nombres_unicos(nombres: Iterable[str], contexto: str) -> None:
    vistos: set[str] = set()
    for nombre in nombres:
        if nombre in vistos:
            raise ValueError(f"El nombre '{nombre}' está repetido en {contexto}.")
        vistos.add(nombre)
