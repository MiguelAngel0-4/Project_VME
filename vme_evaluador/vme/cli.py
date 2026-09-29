"""Punto de entrada de línea de comandos.

Uso:
    python -m vme                                   # modo interactivo
    python -m vme --guardar mi_arbol.json           # interactivo y guarda el árbol
    python -m vme --archivo ejemplos/thompson_simple.json
    python -m vme --archivo costos.json --criterio min
"""

from __future__ import annotations

import argparse
import contextlib
import sys
from collections.abc import Sequence
from pathlib import Path

from .consola import ConstructorInteractivo
from .evaluador import EvaluadorVME
from .modelo import Criterio
from .presentacion import formatear_arbol, formatear_resumen
from .serializacion import ErrorFormato, cargar_arbol, guardar_arbol

CODIGO_OK = 0
CODIGO_ERROR = 1
CODIGO_CANCELADO = 130


def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vme",
        description="Evalúa árboles de decisión con el Valor Monetario Esperado (VME).",
    )
    parser.add_argument(
        "-a",
        "--archivo",
        type=Path,
        help="archivo JSON con el árbol; si se omite, se construye de forma interactiva",
    )
    parser.add_argument(
        "-c",
        "--criterio",
        choices=[c.value for c in Criterio],
        help="sobrescribe el criterio: 'max' (beneficio) o 'min' (costo)",
    )
    parser.add_argument(
        "-g",
        "--guardar",
        type=Path,
        help="guarda en JSON el árbol construido de forma interactiva",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    _configurar_utf8()
    args = crear_parser().parse_args(argv)

    try:
        if args.archivo:
            raiz, criterio = cargar_arbol(args.archivo)
        else:
            raiz, criterio = ConstructorInteractivo().construir()
            if args.guardar:
                guardar_arbol(args.guardar, raiz, criterio)
                print(f"\nÁrbol guardado en '{args.guardar}'.")
    except (ErrorFormato, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return CODIGO_ERROR
    except (KeyboardInterrupt, EOFError):
        print("\nOperación cancelada por el usuario.", file=sys.stderr)
        return CODIGO_CANCELADO

    if args.criterio:
        criterio = Criterio(args.criterio)

    resultado = EvaluadorVME(criterio).evaluar(raiz)
    print()
    print(formatear_arbol(resultado.arbol))
    print()
    print(formatear_resumen(resultado))
    return CODIGO_OK


def _configurar_utf8() -> None:
    """Evita errores con los símbolos del árbol en consolas de Windows."""
    for flujo in (sys.stdout, sys.stderr):
        reconfigurar = getattr(flujo, "reconfigure", None)
        if reconfigurar is not None:
            with contextlib.suppress(OSError, ValueError):
                reconfigurar(encoding="utf-8")
