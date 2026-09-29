# Evaluador de Árboles de Decisión (VME)

Herramienta de consola en Python que calcula el **Valor Monetario Esperado (VME)**
de cada alternativa de un árbol de decisión y recomienda la ruta óptima, ya sea
para **maximizar beneficios** o **minimizar costos**.

Soporta árboles anidados (decisiones dentro de escenarios, azar dentro de azar),
costos fijos por alternativa (inversiones, estudios) y detección de empates.

## Requisitos

Python 3.10 o superior. No usa librerías externas.

## Uso

Desde la carpeta del proyecto:

```bash
python -m vme                                         # construir el árbol paso a paso
python -m vme --guardar mi_arbol.json                 # ... y guardarlo en JSON
python -m vme --archivo ejemplos/thompson_simple.json # evaluar un árbol guardado
python -m vme -a ejemplos/proveedores_costos.json -c min
```

## Cómo se calcula (inducción hacia atrás)

| Nodo | Símbolo | Valor |
|------|---------|-------|
| Terminal | ◁ | el pago |
| Azar | ○ | Σ probabilidad × VME del escenario |
| Decisión | □ | la mejor alternativa (máx. o mín.) tras aplicar su costo |

El costo de una alternativa se **resta** al maximizar y se **suma** al minimizar.

## Formato JSON

```json
{
  "criterio": "max",
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
```

`"pago"` es un atajo para una hoja; `"nodo"` permite anidar cualquier tipo de nodo.

## Estructura

```
vme/
  modelo.py         Nodos inmutables con validación (probabilidades, nombres, costos)
  evaluador.py      Cálculo del VME y extracción de la estrategia óptima
  serializacion.py  Lectura/escritura JSON con errores que indican la ubicación
  consola.py        Constructor interactivo (entrada/salida inyectables)
  presentacion.py   Dibujo del árbol y resumen de resultados
  cli.py            Argumentos de línea de comandos
tests/              40 pruebas (pytest)
ejemplos/           Casos listos para evaluar
```

## Desarrollo

```bash
pip install -e ".[dev]"
pytest            # pruebas + doctests
ruff check .      # estilo y errores comunes
mypy vme          # tipos (modo estricto)
```
