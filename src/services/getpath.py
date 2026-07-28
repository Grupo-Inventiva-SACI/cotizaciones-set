from pathlib import Path
import sys

# Captura la ruta de la app
def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parents[2]

# Test only: captura la ruta del actual ejecutable
def executable_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()

    return Path(__file__).resolve()

# Acceso directo al .env
def env_path() -> Path:
    return app_root() / ".env"