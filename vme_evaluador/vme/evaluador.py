"""Cálculo del Valor Monetario Esperado (VME) por inducción hacia atrás.

El árbol se recorre desde las hojas hacia la raíz ("rollback"):

* Nodo terminal: VME = pago.
* Nodo de azar:  VME = Σ probabilidad_i × VME(escenario_i).
* Nodo de decisión: VME = mejor(VME(alternativa_j) ∓ costo_j),
  donde "mejor" es ``max`` o ``min`` según el criterio.

El resultado es un árbol paralelo (``NodoEvaluado``) que conserva el VME de
cada nodo y marca las alternativas óptimas, más la estrategia recomendada.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum

from .modelo import Criterio, Nodo, NodoAzar, NodoDecision, NodoTerminal

TOLERANCIA_EMPATE = 1e-9


class TipoNodo(str, Enum):
    DECISION = "decision"
    AZAR = "azar"
    TERMINAL = "terminal"


@dataclass(frozen=True)
class RamaEvaluada:
    """Rama del árbol evaluado.

    ``valor`` es lo que la rama aporta al nodo padre: para una alternativa es
    el VME neto (ya aplicado su costo); para un escenario es el VME del hijo.
    """

    etiqueta: str
    valor: float
    nodo: NodoEvaluado
    probabilidad: float | None = None
    costo: float = 0.0
    es_optima: bool = False


@dataclass(frozen=True)
class NodoEvaluado:
    nombre: str
    tipo: TipoNodo
    vme: float
    ramas: tuple[RamaEvaluada, ...] = ()


@dataclass(frozen=True)
class Recomendacion:
    """Decisión óptima en un nodo de decisión alcanzable por la estrategia."""

    nodo: str
    alternativa: str
    vme: float
    contexto: tuple[str, ...] = ()
    """Escenarios que deben ocurrir para llegar a esta decisión."""
    empates: tuple[str, ...] = ()
    """Otras alternativas con exactamente el mismo VME."""


@dataclass(frozen=True)
class ResultadoEvaluacion:
    criterio: Criterio
    arbol: NodoEvaluado
    estrategia: tuple[Recomendacion, ...]

    @property
    def vme_optimo(self) -> float:
        return self.arbol.vme

    @property
    def alternativa_optima(self) -> str | None:
        """Alternativa elegida en la raíz (``None`` si la raíz no es de decisión)."""
        return self.estrategia[0].alternativa if self.estrategia and not self.estrategia[0].contexto else None


class EvaluadorVME:
    """Evalúa árboles de decisión según un criterio de optimización."""

    def __init__(self, criterio: Criterio = Criterio.MAXIMIZAR) -> None:
        self.criterio = criterio

    def evaluar(self, raiz: Nodo) -> ResultadoEvaluacion:
        arbol = self._evaluar_nodo(raiz)
        estrategia = tuple(extraer_estrategia(arbol))
        return ResultadoEvaluacion(self.criterio, arbol, estrategia)

    # ------------------------------------------------------------------ #
    def _evaluar_nodo(self, nodo: Nodo) -> NodoEvaluado:
        match nodo:
            case NodoTerminal():
                return NodoEvaluado(nodo.nombre, TipoNodo.TERMINAL, nodo.pago)
            case NodoAzar():
                return self._evaluar_azar(nodo)
            case NodoDecision():
                return self._evaluar_decision(nodo)
            case _:
                raise TypeError(f"Tipo de nodo no soportado: {type(nodo).__name__}")

    def _evaluar_azar(self, nodo: NodoAzar) -> NodoEvaluado:
        ramas = []
        for escenario in nodo.escenarios:
            hijo = self._evaluar_nodo(escenario.nodo)
            ramas.append(
                RamaEvaluada(
                    etiqueta=escenario.nombre,
                    valor=hijo.vme,
                    nodo=hijo,
                    probabilidad=escenario.probabilidad,
                )
            )
        vme = math.fsum(r.probabilidad * r.valor for r in ramas if r.probabilidad is not None)
        return NodoEvaluado(nodo.nombre, TipoNodo.AZAR, vme, tuple(ramas))

    def _evaluar_decision(self, nodo: NodoDecision) -> NodoEvaluado:
        candidatas = []
        for alternativa in nodo.alternativas:
            hijo = self._evaluar_nodo(alternativa.nodo)
            valor = self._aplicar_costo(hijo.vme, alternativa.costo)
            candidatas.append((alternativa, hijo, valor))

        elegir = max if self.criterio is Criterio.MAXIMIZAR else min
        mejor = elegir(valor for _, _, valor in candidatas)

        ramas = tuple(
            RamaEvaluada(
                etiqueta=alternativa.nombre,
                valor=valor,
                nodo=hijo,
                costo=alternativa.costo,
                es_optima=math.isclose(valor, mejor, rel_tol=TOLERANCIA_EMPATE, abs_tol=TOLERANCIA_EMPATE),
            )
            for alternativa, hijo, valor in candidatas
        )
        return NodoEvaluado(nodo.nombre, TipoNodo.DECISION, mejor, ramas)

    def _aplicar_costo(self, vme: float, costo: float) -> float:
        return vme - costo if self.criterio is Criterio.MAXIMIZAR else vme + costo


def extraer_estrategia(nodo: NodoEvaluado, contexto: tuple[str, ...] = ()) -> Iterator[Recomendacion]:
    """Recorre la ruta óptima y genera una recomendación por cada decisión.

    En un nodo de decisión se sigue solo la alternativa elegida; en un nodo
    de azar se siguen todos los escenarios, porque cualquiera puede ocurrir.
    """
    if nodo.tipo is TipoNodo.DECISION:
        optimas = [rama for rama in nodo.ramas if rama.es_optima]
        elegida = optimas[0]
        yield Recomendacion(
            nodo=nodo.nombre,
            alternativa=elegida.etiqueta,
            vme=nodo.vme,
            contexto=contexto,
            empates=tuple(rama.etiqueta for rama in optimas[1:]),
        )
        yield from extraer_estrategia(elegida.nodo, contexto)
    elif nodo.tipo is TipoNodo.AZAR:
        for rama in nodo.ramas:
            yield from extraer_estrategia(rama.nodo, (*contexto, f"{nodo.nombre} = {rama.etiqueta}"))
