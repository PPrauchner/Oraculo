import io
import tarfile
import zipfile
from pathlib import Path

import pytest

from core.ingestion.source import list_paths, open_directory, read_text


def _make_zip(files: dict[str, str]) -> zipfile.ZipFile:
    """Monta um archive ZIP em memória a partir de um mapa caminho -> conteúdo."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    return zipfile.ZipFile(buffer)


def _make_tar(files: dict[str, str]) -> tarfile.TarFile:
    """Monta um archive TAR em memória a partir de um mapa caminho -> conteúdo."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tf:
        for path, content in files.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=path)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    buffer.seek(0)
    return tarfile.open(fileobj=buffer, mode="r")


def _make_directory(root: Path, files: dict[str, str]) -> Path:
    """Materializa um Projeto-Alvo em disco a partir de um mapa caminho -> conteúdo."""
    for path, content in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


PROJECT = {
    "pyproject.toml": "[project]\nname = 'alvo'\n",
    "main.py": "import requests\n",
    "core/__init__.py": "",
    "core/service.py": "import pandas\n",
    "tests/test_service.py": "import pytest\n",
}


# --- list_paths: caminhos relativos à raiz do Projeto-Alvo, ordenados ---------


def test_list_paths_returns_sorted_relative_paths_from_dict():
    assert list_paths(dict(PROJECT)) == [
        "core/__init__.py",
        "core/service.py",
        "main.py",
        "pyproject.toml",
        "tests/test_service.py",
    ]


def test_list_paths_agrees_across_every_source_kind(tmp_path):
    """Mesmo Projeto-Alvo em ZIP, TAR, diretório e dict devolve os mesmos caminhos."""
    directory = _make_directory(tmp_path / "alvo", dict(PROJECT))

    assert (
        list_paths(_make_zip(dict(PROJECT)))
        == list_paths(_make_tar(dict(PROJECT)))
        == list_paths(directory)
        == list_paths(dict(PROJECT))
    )


def test_list_paths_strips_the_single_wrapper_folder_of_an_archive():
    """ZIP do GitHub embrulha tudo em `<repo>-<branch>/`; a raiz é dentro dela."""
    wrapped = {f"grupo-03-main/{path}": content for path, content in PROJECT.items()}

    assert list_paths(_make_zip(wrapped)) == list_paths(dict(PROJECT))


def test_list_paths_keeps_a_root_that_is_itself_a_package():
    """Pasta de topo com `__init__.py` é Módulo Próprio, não embrulho."""
    files = {"core/__init__.py": "", "core/service.py": ""}

    assert list_paths(dict(files)) == ["core/__init__.py", "core/service.py"]


def test_list_paths_omits_directory_entries():
    """Entradas de pasta do archive não são arquivos do Projeto-Alvo."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("core/", "")
        zf.writestr("core/__init__.py", "")
        zf.writestr("main.py", "")

    assert list_paths(zipfile.ZipFile(buffer)) == ["core/__init__.py", "main.py"]


def test_list_paths_ignores_environment_and_cache_folders(tmp_path):
    """Ambiente virtual e cache não são o Projeto-Alvo, nem em disco nem em archive."""
    noisy = {
        "main.py": "",
        ".venv/lib/site-packages/requests/__init__.py": "",
        "__pycache__/main.cpython-311.pyc": "",
        ".git/config": "",
        "node_modules/left-pad/index.js": "",
    }
    directory = _make_directory(tmp_path / "alvo", dict(noisy))

    assert list_paths(directory) == ["main.py"]
    assert list_paths(_make_zip(dict(noisy))) == ["main.py"]


def test_list_paths_normalizes_windows_separators_and_dot_prefix():
    files = {".\\main.py": "", "core\\helpers.py": ""}

    assert list_paths(dict(files)) == ["core/helpers.py", "main.py"]


def test_read_text_uniformizes_line_endings(tmp_path):
    """Diretório no Windows traria "\\r\\n" onde o archive traz "\\n"."""
    directory = tmp_path / "alvo"
    directory.mkdir()
    (directory / "requirements.txt").write_bytes(b"requests==2.0\r\npandas==3.0\r\n")

    assert read_text(directory, "requirements.txt") == "requests==2.0\npandas==3.0\n"


def test_list_paths_of_an_unsupported_source_is_empty():
    assert list_paths(object()) == []


# --- read_text: leitura por caminho, nunca por membro -------------------------


def test_read_text_reads_by_path_across_every_source_kind(tmp_path):
    directory = _make_directory(tmp_path / "alvo", dict(PROJECT))

    for source in (
        _make_zip(dict(PROJECT)),
        _make_tar(dict(PROJECT)),
        directory,
        dict(PROJECT),
    ):
        assert read_text(source, "core/service.py") == "import pandas\n"


def test_read_text_uses_the_root_relative_path_of_a_wrapped_archive():
    """O chamador só conhece o caminho relativo à raiz; o embrulho é interno."""
    wrapped = {f"grupo-03-main/{path}": content for path, content in PROJECT.items()}

    assert read_text(_make_zip(wrapped), "core/service.py") == "import pandas\n"


def test_read_text_of_an_unknown_path_is_none():
    assert read_text(dict(PROJECT), "nao/existe.py") is None


def test_read_text_of_an_unsupported_source_is_none():
    assert read_text(object(), "main.py") is None


def test_read_text_survives_undecodable_bytes():
    """Arquivo com bytes inválidos não interrompe a auditoria."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("main.py", b"import requests\n\xff\xfe")

    assert "requests" in read_text(zipfile.ZipFile(buffer), "main.py")


# --- open_directory: erros claros, sem exceção vazando para a UI --------------


def test_open_directory_accepts_a_readable_project_directory(tmp_path):
    directory = _make_directory(tmp_path / "alvo", dict(PROJECT))

    source, error = open_directory(str(directory))

    assert error == ""
    assert source == directory


def test_open_directory_rejects_a_missing_path(tmp_path):
    source, error = open_directory(str(tmp_path / "nao-existe"))

    assert source is None
    assert "não encontrado" in error


def test_open_directory_rejects_a_file(tmp_path):
    target = tmp_path / "projeto.zip"
    target.write_text("", encoding="utf-8")

    source, error = open_directory(str(target))

    assert source is None
    assert "não é um diretório" in error


def test_open_directory_rejects_an_empty_path():
    source, error = open_directory("   ")

    assert source is None
    assert error != ""


def test_open_directory_rejects_a_directory_that_is_not_a_python_project(tmp_path):
    """Apontar para uma pasta qualquer não pode custar uma varredura do disco."""
    (tmp_path / "fotos").mkdir()
    (tmp_path / "notas.txt").write_text("", encoding="utf-8")

    source, error = open_directory(str(tmp_path))

    assert source is None
    assert "não parece um projeto Python" in error


def test_open_directory_does_not_walk_the_tree_to_decide(tmp_path, monkeypatch):
    """A checagem é só do primeiro nível: nada de os.walk antes de aceitar."""
    (tmp_path / "pyproject.toml").write_text("[project]\n", encoding="utf-8")

    def _fail(*_args, **_kwargs):
        raise AssertionError("open_directory percorreu a árvore inteira")

    monkeypatch.setattr("os.walk", _fail)

    source, error = open_directory(str(tmp_path))

    assert error == ""
    assert source == tmp_path


def test_open_directory_accepts_a_project_declared_only_by_requirements(tmp_path):
    (tmp_path / "requirements-dev.txt").write_text("pytest\n", encoding="utf-8")

    source, error = open_directory(str(tmp_path))

    assert error == ""
    assert source == tmp_path


def test_read_text_of_a_directory_does_not_rewalk_the_tree(tmp_path, monkeypatch):
    """Ler N arquivos não pode custar N varreduras do diretório."""
    (tmp_path / "main.py").write_text("import requests\n", encoding="utf-8")

    def _fail(*_args, **_kwargs):
        raise AssertionError("read_text percorreu a árvore para ler um arquivo")

    monkeypatch.setattr("os.walk", _fail)

    assert read_text(tmp_path, "main.py") == "import requests\n"


def test_read_text_of_a_directory_refuses_to_escape_the_project_root(tmp_path):
    """Um caminho com `..` não pode ler fora do Projeto-Alvo."""
    (tmp_path / "segredo.txt").write_text("senha", encoding="utf-8")
    root = tmp_path / "alvo"
    root.mkdir()

    assert read_text(root, "../segredo.txt") is None


def test_read_text_of_a_directory_refuses_environment_folders(tmp_path):
    """O que `list_paths` não oferece, `read_text` não entrega."""
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "pyvenv.cfg").write_text("home = /usr", encoding="utf-8")

    assert read_text(tmp_path, ".venv/pyvenv.cfg") is None


@pytest.mark.skipif(
    not hasattr(Path, "chmod"), reason="permissões não simuláveis nesta plataforma"
)
def test_open_directory_rejects_an_unreadable_directory(tmp_path, monkeypatch):
    """Sem permissão de leitura: mensagem clara, não PermissionError."""
    directory = _make_directory(tmp_path / "alvo", dict(PROJECT))

    def _deny(*_args, **_kwargs):
        raise PermissionError("acesso negado")

    monkeypatch.setattr("os.scandir", _deny)

    source, error = open_directory(str(directory))

    assert source is None
    assert "permissão" in error
