_DEFAULT_IGNORED_DIRS = [
    ".venv",
    "venv",
    ".env",
    "env",
    "__pycache__",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    ".eggs",
]

_DEFAULT_IGNORED_SUFFIXES = [".egg-info"]

_CONFIG_FILES = {"requirements.txt", "pyproject.toml", "uv .lock"}

PYPI_BASE_URL = "https://pypi.org/pypi"
