"""Construcción interactiva de un árbol de decisión desde la consola.

Las funciones de entrada y salida se inyectan en el constructor, lo que
permite probar el diálogo completo sin teclado (ver ``tests/``).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import TypeVar

from .modelo import (
    TOLERANCIA_PROBABILIDAD,
    Alternativa,
    Criterio,
    Escenario,
    Nodo,
    NodoAzar,
    NodoDecision,
    NodoTerminal,
)

Entrada = Callable[[str], str]
Salida = Callable[[str], None]
T = TypeVar("T")


def convertir_numero(texto: str) -> float:
    """Convierte texto a número aceptando '$', '_', coma decimal y porcentajes.

    >>> convertir_numero("-180000")
    -180000.0
    >>> convertir_numero("0,25")
    0.25
    >>> convertir_numero("45%")
    0.45
    """
    limpio = texto.strip().replace(" ", "").replace("_", "").replace("$", "")
    es_porcentaje = limpio.endswith("%")
    if es_porcentaje:
        limpio = limpio[:-1]
    if "," in limpio and "." not in limpio:
        limpio = limpio.replace(",", ".")
    try:
        valor = float(limpio)
    except ValueError:
        raise ValueError(f"'{texto}' no es un número válido.") from None
    if not math.isfinite(valor):
        raise ValueError("El número debe ser finito.")
    return valor / 100 if es_porcentaje else valor


class ConstructorInteractivo:
    """Guía al usuario, paso a paso, para definir un árbol de decisión."""

    def __init__(self, entrada: Entrada = input, salida: Salida = print) -> None:
        self._entrada = entrada
        self._salida = salida

    def construir(self) -> tuple[NodoDecision, Criterio]:
        self._salida("=== Constructor de árboles de decisión (VME) ===")
        self._salida("Escribe los montos SIN separador de miles (ej.: 200000 o -180000.50).")
        self._salida("Las probabilidades pueden ir como 0.3 o como 30%.\n")
        criterio = self._pedir_opcion(
            "¿Qué deseas optimizar?",
            {
                "1": ("Maximizar beneficio (pagos = ganancias)", Criterio.MAXIMIZAR),
                "2": ("Minimizar costo (pagos = costos)", Criterio.MINIMIZAR),
            },
            nivel=0,
        )
        return self._construir_decision(nivel=0), criterio

    # ------------------------------------------------------------------ #
    # Construcción de nodos
    # ------------------------------------------------------------------ #
    def _construir_nodo(self, nombre_rama: str, nivel: int) -> Nodo:
        tipo = self._pedir_opcion(
            f"¿Qué ocurre después de '{nombre_rama}'?",
            {
                "1": ("Pago final (resultado monetario)", "terminal"),
                "2": ("Nodo de azar (escenarios con probabilidades)", "azar"),
                "3": ("Nueva decisión", "decision"),
            },
            nivel,
        )
        if tipo == "terminal":
            pago = self._pedir_numero(f"Pago de '{nombre_rama}'", nivel)
            return NodoTerminal(nombre_rama, pago)
        if tipo == "azar":
            return self._construir_azar(nivel)
        return self._construir_decision(nivel)

    def _construir_decision(self, nivel: int) -> NodoDecision:
        self._mostrar("□ NODO DE DECISIÓN", nivel)
        nombre = self._pedir_texto("Nombre de la decisión", nivel)
        cantidad = self._pedir_entero("¿Cuántas alternativas tiene?", nivel, minimo=2)
        usados: set[str] = set()
        alternativas = []
        for i in range(1, cantidad + 1):
            nombre_alt = self._pedir_nombre_unico(f"Alternativa {i} - nombre", usados, nivel + 1)
            costo = self._pedir_numero(
                "Costo fijo de elegirla (inversión)", nivel + 1, por_defecto=0.0, minimo=0.0
            )
            nodo = self._construir_nodo(nombre_alt, nivel + 2)
            alternativas.append(Alternativa(nombre_alt, nodo, costo))
        return NodoDecision(nombre, tuple(alternativas))

    def _construir_azar(self, nivel: int) -> NodoAzar:
        self._mostrar("○ NODO DE AZAR", nivel)
        nombre = self._pedir_texto("Nombre del evento incierto (ej.: Mercado)", nivel)
        cantidad = self._pedir_entero("¿Cuántos escenarios tiene?", nivel, minimo=2)
        definiciones = self._pedir_escenarios(cantidad, nivel + 1)
        escenarios = tuple(
            Escenario(nombre_esc, prob, self._construir_nodo(nombre_esc, nivel + 2))
            for nombre_esc, prob in definiciones
        )
        return NodoAzar(nombre, escenarios)

    def _pedir_escenarios(self, cantidad: int, nivel: int) -> list[tuple[str, float]]:
        """Pide nombres y probabilidades hasta que estas sumen 1."""
        while True:
            usados: set[str] = set()
            definiciones: list[tuple[str, float]] = []
            for i in range(1, cantidad + 1):
                nombre = self._pedir_nombre_unico(f"Escenario {i} - nombre", usados, nivel)
                es_ultimo = i == cantidad
                restante = round(max(0.0, 1.0 - math.fsum(p for _, p in definiciones)), 10)
                prob = self._pedir_numero(
                    f"Probabilidad de '{nombre}'",
                    nivel,
                    por_defecto=restante if es_ultimo else None,
                    minimo=0.0,
                    maximo=1.0,
                )
                definiciones.append((nombre, prob))
            total = math.fsum(p for _, p in definiciones)
            if math.isclose(total, 1.0, abs_tol=TOLERANCIA_PROBABILIDAD):
                return definiciones
            self._mostrar(
                f"⚠ Las probabilidades suman {total:.4g} y deben sumar 1. Ingrésalas de nuevo.", nivel
            )

    # ------------------------------------------------------------------ #
    # Utilidades de entrada con validación
    # ------------------------------------------------------------------ #
    def _mostrar(self, texto: str, nivel: int) -> None:
        self._salida(f"{'  ' * nivel}{texto}")

    def _preguntar(self, mensaje: str, nivel: int) -> str:
        return self._entrada(f"{'  ' * nivel}{mensaje}: ").strip()

    def _pedir_texto(self, mensaje: str, nivel: int) -> str:
        while True:
            if texto := self._preguntar(mensaje, nivel):
                return texto
            self._mostrar("⚠ Este campo no puede quedar vacío.", nivel)

    def _pedir_nombre_unico(self, mensaje: str, usados: set[str], nivel: int) -> str:
        while True:
            nombre = self._pedir_texto(mensaje, nivel)
            if nombre not in usados:
                usados.add(nombre)
                return nombre
            self._mostrar(f"⚠ Ya existe una rama llamada '{nombre}' en este nodo.", nivel)

    def _pedir_numero(
        self,
        mensaje: str,
        nivel: int,
        *,
        por_defecto: float | None = None,
        minimo: float | None = None,
        maximo: float | None = None,
    ) -> float:
        if por_defecto is not None:
            mensaje += f" [Enter = {por_defecto:g}]"
        while True:
            texto = self._preguntar(mensaje, nivel)
            if not texto and por_defecto is not None:
                return por_defecto
            try:
                valor = convertir_numero(texto)
            except ValueError as error:
                self._mostrar(f"⚠ {error}", nivel)
                continue
            if minimo is not None and valor < minimo:
                self._mostrar(f"⚠ El valor debe ser mayor o igual a {minimo:g}.", nivel)
            elif maximo is not None and valor > maximo:
                self._mostrar(f"⚠ El valor debe ser menor o igual a {maximo:g}.", nivel)
            else:
                return valor

    def _pedir_entero(self, mensaje: str, nivel: int, *, minimo: int = 1) -> int:
        while True:
            texto = self._preguntar(mensaje, nivel)
            try:
                valor = int(texto)
            except ValueError:
                self._mostrar(f"⚠ '{texto}' no es un número entero.", nivel)
                continue
            if valor >= minimo:
                return valor
            self._mostrar(f"⚠ Debe ser al menos {minimo}.", nivel)

    def _pedir_opcion(self, mensaje: str, opciones: Mapping[str, tuple[str, T]], nivel: int) -> T:
        self._mostrar(mensaje, nivel)
        for clave, (descripcion, _) in opciones.items():
            self._mostrar(f"  [{clave}] {descripcion}", nivel)
        while True:
            clave = self._preguntar("Opción", nivel)
            if clave in opciones:
                return opciones[clave][1]
            self._mostrar(f"⚠ Opción no válida. Elige entre: {', '.join(opciones)}.", nivel)
