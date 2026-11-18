"""
The Sample Project: a small Target Project that lives in memory, as data.

Responsibilities:
- Hand out the Sample Project as a `dict[str, str]` source (path -> content), the
  in-memory kind `ProjectSource` already accepts (ADR-0006).
- Name it with a fixed identity for the export, independent of the screen language
  (ADR-0008).

Whoever opens ORÁCULO to get to know it rarely has a Python project at hand; the
sample is what shows a full report in one click (issue #58). It is data on purpose,
and not a folder with a real Declaration: a string is neither a Root Import nor a
Declaration, so neither the self-audit nor an audit of this repository sees the
sample's fake dependencies.

What each package is there to show, against the real PyPI:
- `requests`: declared and imported (Healthy) and pinned by the Lock at 2.25.1, from
  2020-12 — checked on PyPI while implementing, the latest was 2.34.2. An old release
  of a stable, active package stays Outdated as time goes by.
- `flask`: declared and never imported (Zombie). Locked at 2.0.0, from 2021-05, so its
  Size and Age appear too.
- `numpy`: imported and never declared (Ghost). Its Import Name is its Distribution
  Name, so the result does not depend on the Import Alias table.
- `urllib3`: only in the Lock, as a transitive. It lends a version and never enters
  the audited set (ADR-0002).
"""

# Identity of the Sample Project in the export. Fixed and in English, like the
# rest of the CSV contract: it does not follow the screen language (ADR-0008).
SAMPLE_PROJECT_NAME = "oraculo-sample-project"

_SAMPLE_FILES: dict[str, str] = {
    "requirements.txt": "requests\nflask\n",
    "uv.lock": (
        "version = 1\n"
        'requires-python = ">=3.11"\n'
        "\n"
        "[[package]]\n"
        'name = "flask"\n'
        'version = "2.0.0"\n'
        "\n"
        "[[package]]\n"
        'name = "requests"\n'
        'version = "2.25.1"\n'
        "\n"
        "[[package]]\n"
        'name = "urllib3"\n'
        'version = "1.26.2"\n'
    ),
    "main.py": (
        '"""Fetches a list of numbers and prints its mean."""\n'
        "\n"
        "import requests\n"
        "\n"
        "from app.stats import mean\n"
        "\n"
        "\n"
        "def main() -> None:\n"
        '    numbers = requests.get("https://example.com/numbers.json").json()\n'
        "    print(mean(numbers))\n"
    ),
    "app/__init__.py": "",
    "app/stats.py": (
        '"""Statistics over the fetched numbers."""\n'
        "\n"
        "import numpy\n"
        "\n"
        "\n"
        "def mean(numbers: list[float]) -> float:\n"
        "    return float(numpy.mean(numbers))\n"
    ),
}


def sample_project() -> dict[str, str]:
    """Hands out the Sample Project as an in-memory Target Project source.

    Returns:
        A fresh copy of the path -> content map: the source goes to the session
        state, and changing one copy must not change the sample.
    """
    return dict(_SAMPLE_FILES)
