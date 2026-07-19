import io
import zipfile

from core.ingestion.filter import (
    get_unique_folders,
    is_path_in_ignored_folders,
    validate_project_structure,
)


def _make_zip(files: dict[str, str]) -> zipfile.ZipFile:
    """Monta um archive ZIP em memória a partir de um mapa caminho -> conteúdo."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    return zipfile.ZipFile(buffer)


PROJECT = {
    "pyproject.toml": "[project]\nname = 'alvo'\n",
    "main.py": "import requests\n",
    "core/__init__.py": "",
    "core/service.py": "",
    "tests/test_service.py": "",
    "src/tests/test_helpers.py": "",
    "docs/adr/0001.md": "",
}


# --- get_unique_folders: só oferece o que o filtro sabe excluir ---------------


def test_get_unique_folders_lists_every_folder_of_the_project():
    assert get_unique_folders(dict(PROJECT)) == [
        "adr",
        "core",
        "docs",
        "src",
        "tests",
    ]


def test_get_unique_folders_of_an_empty_source_is_empty():
    assert get_unique_folders({}) == []


def test_every_offered_folder_actually_excludes_something():
    """AC da #26: nenhuma pasta oferecida no multiselect falha em silêncio."""
    paths = list(PROJECT)

    for folder in get_unique_folders(dict(PROJECT)):
        assert any(is_path_in_ignored_folders(path, [folder]) for path in paths), (
            f"a pasta {folder!r} é oferecida mas não exclui nada"
        )


def test_get_unique_folders_ignores_the_wrapper_folder_of_an_archive():
    """A pasta-embrulho não é pasta do Projeto-Alvo: some na normalização."""
    wrapped = {f"grupo-03-main/{path}": content for path, content in PROJECT.items()}

    assert "grupo-03-main" not in get_unique_folders(_make_zip(wrapped))


# --- is_path_in_ignored_folders: casa por segmento, em qualquer profundidade --


def test_ignores_a_top_level_folder():
    assert is_path_in_ignored_folders("tests/test_service.py", ["tests"]) is True


def test_ignores_a_nested_folder_of_the_same_name():
    """Issue #26: `src/tests` também é Exclusão quando o usuário marca `tests`."""
    assert is_path_in_ignored_folders("src/tests/test_helpers.py", ["tests"]) is True


def test_ignores_a_folder_at_any_depth():
    assert is_path_in_ignored_folders("docs/adr/0001.md", ["adr"]) is True


def test_keeps_a_path_outside_every_exclusion():
    assert is_path_in_ignored_folders("core/service.py", ["tests", "docs"]) is False


def test_a_file_whose_name_matches_an_exclusion_is_kept():
    """Exclusão é pasta: um arquivo chamado `tests` não é excluído."""
    assert is_path_in_ignored_folders("tests", ["tests"]) is False


def test_a_folder_whose_prefix_matches_an_exclusion_is_kept():
    """`tests_helpers/` não é `tests/`."""
    assert is_path_in_ignored_folders("tests_helpers/x.py", ["tests"]) is False


def test_no_exclusion_keeps_everything():
    assert is_path_in_ignored_folders("tests/test_service.py", []) is False


def test_an_empty_path_is_never_excluded():
    assert is_path_in_ignored_folders("", ["tests"]) is False


def test_exclusion_accepts_a_folder_written_with_separators():
    """O usuário pode digitar `tests/` ou `./tests`; vale o nome da pasta."""
    assert is_path_in_ignored_folders("tests/test_service.py", ["./tests/"]) is True


# --- validate_project_structure: mensagens neutras quanto à fonte -------------


def test_a_project_with_code_and_a_declaration_is_valid():
    assert validate_project_structure(dict(PROJECT)) == (True, "")


def test_a_directory_source_is_validated_like_an_archive(tmp_path):
    (tmp_path / "main.py").write_text("import requests\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    assert validate_project_structure(tmp_path) == (True, "")


def test_a_project_without_python_files_is_invalid():
    is_valid, error = validate_project_structure({"pyproject.toml": ""})

    assert is_valid is False
    assert "ZIP" not in error
    assert ".py" in error


def test_a_project_without_a_declaration_is_invalid():
    is_valid, error = validate_project_structure({"main.py": "import requests\n"})

    assert is_valid is False
    assert "ZIP" not in error
    assert "dependências" in error


def test_an_empty_project_is_invalid():
    is_valid, error = validate_project_structure({})

    assert is_valid is False
    assert "ZIP" not in error


def test_an_unsupported_source_kind_is_diagnosed_as_such():
    """Espécie de fonte não suportada não é "Projeto-Alvo sem arquivo .py".

    Sem essa mensagem, `_raw_paths` devolve [] e o usuário recebe um diagnóstico
    falso sobre o conteúdo de um Projeto-Alvo que sequer chegou a ser aberto.
    """
    is_valid, error = validate_project_structure(object())

    assert is_valid is False
    assert ".py" not in error
    assert "não suportada" in error


def test_a_missing_source_is_invalid():
    is_valid, error = validate_project_structure(None)

    assert is_valid is False
    assert error != ""


def test_a_project_whose_only_code_is_in_an_exclusion_is_invalid():
    """Código em Exclusão não conta para os requisitos mínimos."""
    files = {"pyproject.toml": "", "tests/test_service.py": ""}

    is_valid, _error = validate_project_structure(files, ["tests"])

    assert is_valid is False
