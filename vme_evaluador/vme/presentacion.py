"""Formateo en texto del árbol evaluado y del resumen de resultados.

Estas funciones solo construyen cadenas (no imprimen), para mantener la
lógica de presentación separada de la entrada/salida y facilitar las pruebas.
"""

from __future__ import annotations

from .evaluador import NodoEvaluado, RamaEvaluada, ResultadoEvaluacion, TipoNodo

SIMBOLOS = {TipoNodo.DECISION: "□", TipoNodo.AZAR: "○", TipoNodo.TERMINAL: "◁"}
MARCA_OPTIMA = "★"


def formatear_moneda(valor: float) -> str:
    if abs(valor) < 0.005:  # evita mostrar "-$0.00"
        valor = 0.0
    signo = "-" if valor < 0 else ""
    return f"{signo}${abs(valor):,.2f}"


def formatear_arbol(arbol: NodoEvaluado) -> str:
    lineas = [_describir_nodo(arbol)]
    _agregar_ramas(arbol, "", lineas)
    return "\n".join(lineas)


def _describir_nodo(nodo: NodoEvaluado) -> str:
    return f"{SIMBOLOS[nodo.tipo]} {nodo.nombre}   [VME = {formatear_moneda(nodo.vme)}]"


def _describir_rama(rama: RamaEvaluada) -> str:
    if rama.probabilidad is not None:  # escenario de un nodo de azar
        texto = f"{rama.etiqueta} (p = {rama.probabilidad:.4g})"
    else:  # alternativa de un nodo de decisión
        marca = f"{MARCA_OPTIMA} " if rama.es_optima else ""
        costo = f", costo {formatear_moneda(rama.costo)}" if rama.costo else ""
        texto = f"{marca}{rama.etiqueta} (VME neto {formatear_moneda(rama.valor)}{costo})"
    if rama.nodo.tipo is TipoNodo.TERMINAL:
        texto += f"  {SIMBOLOS[TipoNodo.TERMINAL]} {formatear_moneda(rama.nodo.vme)}"
    return texto


def _agregar_ramas(nodo: NodoEvaluado, prefijo: str, lineas: list[str]) -> None:
    for indice, rama in enumerate(nodo.ramas):
        es_ultima = indice == len(nodo.ramas) - 1
        lineas.append(prefijo + ("└── " if es_ultima else "├── ") + _describir_rama(rama))
        if rama.nodo.tipo is not TipoNodo.TERMINAL:
            continuacion = prefijo + ("    " if es_ultima else "│   ")
            lineas.append(continuacion + "└── " + _describir_nodo(rama.nodo))
            _agregar_ramas(rama.nodo, continuacion + "    ", lineas)


def formatear_resumen(resultado: ResultadoEvaluacion) -> str:
    raiz = resultado.arbol
    separador = "=" * 64
    lineas = [separador, "RESULTADO DEL ANÁLISIS", separador, f"Criterio: {resultado.criterio.descripcion}"]

    if raiz.tipo is TipoNodo.DECISION:
        lineas += ["", f"VME de cada alternativa en «{raiz.nombre}»:"]
        ancho = max(len(rama.etiqueta) for rama in raiz.ramas)
        for rama in raiz.ramas:
            marca = MARCA_OPTIMA if rama.es_optima else " "
            lineas.append(f"  {marca} {rama.etiqueta:<{ancho}}  {formatear_moneda(rama.valor):>18}")

    if resultado.estrategia:
        lineas += ["", "Estrategia óptima:"]
        for numero, rec in enumerate(resultado.estrategia, start=1):
            condicion = f"Si {' y '.join(rec.contexto)} → en" if rec.contexto else "En"
            lineas.append(
                f"  {numero}. {condicion} «{rec.nodo}» elegir «{rec.alternativa}» "
                f"(VME = {formatear_moneda(rec.vme)})"
            )
            if rec.empates:
                lineas.append(f"     Empate: también es óptima {', '.join(f'«{e}»' for e in rec.empates)}.")

    lineas += ["", f"VME ÓPTIMO: {formatear_moneda(resultado.vme_optimo)}", separador]
    return "\n".join(lineas)
