from pathlib import Path

import pytest

CARPETA_EJEMPLOS = Path(__file__).resolve().parent.parent / "ejemplos"


@pytest.fixture
def ejemplos() -> Path:
    return CARPETA_EJEMPLOS
