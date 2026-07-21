*[Versão em português](Enunciado.md)*

# Assignment

Python projects accumulate dependencies over time, and it is common for libraries to become
outdated, unused or to carry known vulnerabilities.

The goal of this project is to develop a tool that:
1. Analyses dependency configuration files (pyproject.toml or requirements.txt) and the
   project's source code.
2. Crosses the declared dependencies with the real imports found in the source code.
3. Identifies three situations:
    a) Dependencies declared but not used in the code ("zombie" dependencies).
    b) Imports used in the code but not declared as dependencies ("ghost" dependencies).
    c) Dependencies with outdated versions.

The version check must be done by querying the PyPI repository to verify the latest available
version. The system must let the user configure files and directories to be ignored (e.g.,
tests/, docs/), so that the analysis focuses only on the target project's main code.

The tool must:

1. Generate a structured report, in a graphical interface, indicating:
    a) Total dependencies
        - List of dependencies
        - Count
        - Size
        - Age (current date - release date of the used version)
    b) Zombie dependencies
        - List of dependencies
        - Count
        - Size
        - Age (current date - release date of the used version)
    c) Ghost dependencies
        - List of dependencies
        - Count
        - Size
        - Age (current date - release date of the used version)

2. Allow exporting a report for tracking over time. The report must:
    a) Be viewable in a graphical interface
    b) Be exportable to CSV

User Stories
01. As a developer, I want to select a Python project by pointing to the code directory, so
    that the tool analyses the dependencies and the imports.
02. As a developer, I want the tool to ignore configured files and directories (e.g., tests/,
    docs/), to focus the analysis on the main code.
03. As a developer, I want the tool to cross the declared dependencies with the imports found
    in the code, to identify dependencies that are declared but not used (zombie
    dependencies).
04. As a developer, I want the tool to identify imports used in the code but not declared as
    dependencies, to avoid failures in other environments (ghost dependencies).
05. As a developer, I want the tool to query an external data source (i.e., PyPI) to check
    whether the dependencies used in the project are outdated, to assess the need for updates.
06. As a developer, I want to view a structured report in a graphical interface with
    indicators about the dependencies to quickly understand the project's health. I want the
    report to include, at a minimum, statistics on the number of dependencies, size and age
    of the dependencies, with information stratified by category (total, zombies, ghosts,
    outdated).
07. As a developer, I want to export the project's dependency report in CSV format, to track
    its evolution over time and perform complementary analyses.

Implementation Rules
01. The project must be implemented in Python, using the procedural programming paradigm.
02. Dependency analysis must be done by scanning the configuration files (e.g., pyproject.toml
    and requirements.txt) and the source code (.py files) of the project.
03. The dependency version lookup must use the public PyPI API
    (https://pypi.org/pypi/DEPENDENCY_NAME/json).
04. Project configuration (root directory, exclusions) must be done through a graphical
    interface.
05. The project must be implemented in a modular way, with functions and modules separated
    according to the responsibilities of each part of the system.

Implementation Tips
01. Use tools such as uv (https://uv.pypa.io/) or Poetry (https://python-poetry.org/) to
    manage the virtual environment and the system's dependencies.
02. Explore Python libraries such as Streamlit (http://streamlit.io/) and Gradio
    (https://gradio.app/) to build the graphical interface.
03. Use Python's native file-reading or code-manipulation modules to handle the source code of
    the input project whose dependencies will be analysed.

Key Concepts
01. Software dependencies.
02. Management of virtual environments and dependencies.
03. Definition of graphical interfaces.
04. File manipulation.
05. Consumption of external APIs.
06. Code modularisation.
