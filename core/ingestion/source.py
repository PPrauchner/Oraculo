"""
A fonte de arquivos do Projeto-Alvo, reduzida a duas primitivas.

Responsabilidades:
- Listar os caminhos do Projeto-Alvo, relativos à sua raiz (`list_paths`).
- Ler o conteúdo de um arquivo pelo caminho (`read_text`).
- Abrir um diretório local como fonte, com erro legível (`open_directory`).

Único módulo do projeto autorizado a conhecer `ZipFile`/`TarFile`: o despacho por
`isinstance` fica confinado aqui (ADR-0006). Quem consome pede caminho e conteúdo,
e por isso funciona igual nos dois modos de ingestão do ADR-0001.

**Ler por caminho, e não por membro, é o que mata o acoplamento**: enquanto a leitura
pedisse um `ZipInfo`/`TarInfo`, o tipo vazava para o chamador. A preguiça é preservada
— percorrer o índice é barato, decodificar cada arquivo não, então `read_text` só é
chamada para o que passou pelo filtro.

Tamanho e Idade **não** entram no contrato: vêm do PyPI, não do disco (ADR-0004).
"""

import os
import tarfile
import zipfile
from pathlib import Path
from weakref import WeakKeyDictionary

# As espécies de fonte que o despacho reconhece (ADR-0006). `dict` mapeia caminho a
# conteúdo e serve de dublê nos testes, sem construir um archive de verdade.
ProjectSource = zipfile.ZipFile | tarfile.TarFile | Path | dict[str, str]

# Pastas que nunca fazem parte do Projeto-Alvo: ambiente virtual, cache de
# ferramenta e metadados de VCS. Um diretório em disco as carrega e um archive
# normalmente não; ignorá-las nos dois lados é o que faz diretório e ZIP
# auditarem o mesmo Projeto-Alvo (ADR-0001).
NON_PROJECT_FOLDERS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        "node_modules",
        ".idea",
        ".vscode",
        "site-packages",
    }
)

# Arquivos que, na raiz, denunciam um projeto Python
PROJECT_MARKERS = frozenset(
    {
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "environment.yml",
        "environment.yaml",
        "pipfile",
    }
)


def _normalize(raw_path: str) -> str:
    """Uniformiza um caminho cru vindo de qualquer espécie de fonte.

    Args:
        raw_path: Caminho como a fonte o entrega, possivelmente com separador do
            Windows, prefixo "./" ou barra final.

    Returns:
        Caminho com separador "/", sem prefixo "./" e sem barra final. String
        vazia quando nada sobra.
    """
    clean = raw_path.replace("\\", "/").strip("/")
    while clean.startswith("./"):
        clean = clean[2:]
    return clean


def _is_project_path(path: str) -> bool:
    """Indica se um caminho pertence ao Projeto-Alvo, e não ao ambiente ao redor."""
    return not any(segment in NON_PROJECT_FOLDERS for segment in path.split("/"))


def _decode(data: bytes) -> str:
    """Decodifica o conteúdo de um arquivo, uniformizando o fim de linha.

    O mesmo Projeto-Alvo lido de um diretório no Windows traria "\\r\\n" onde o
    archive traz "\\n", e o "\\r" residual entraria no Nome de Distribuição de uma
    Declaração lida linha a linha.

    Args:
        data: Bytes crus do arquivo.

    Returns:
        Texto com bytes inválidos descartados e fim de linha "\\n".
    """
    text = data.decode("utf-8", errors="ignore")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _looks_like_a_python_project(directory: Path) -> bool:
    """Indica se a raiz do diretório tem marca de projeto Python.

    Olha só o primeiro nível, de propósito: é a checagem barata que impede o
    Baita Auditor de percorrer uma árvore enorme (a pasta do usuário, um disco
    inteiro) antes de descobrir que ali não há Projeto-Alvo algum.

    Args:
        directory: Diretório apontado pelo usuário.

    Returns:
        True se houver, na raiz, um arquivo .py, uma Declaração ou um Lock.
    """
    with os.scandir(directory) as entries:
        for entry in entries:
            if not entry.is_file():
                continue

            name = entry.name.lower()
            if name in PROJECT_MARKERS or name.endswith((".py", ".lock")):
                return True
            if name.startswith("requirements") and name.endswith(".txt"):
                return True

    return False


def _project_root_prefix(paths: list[str]) -> str:
    """Descobre a pasta que apenas embrulha o Projeto-Alvo, se houver.

    Um archive normalmente contém tudo dentro de uma única pasta raiz
    (`grupo-03-main/core/...`) — é o formato que o "Download ZIP" do GitHub produz.
    Nesse caso a raiz do Projeto-Alvo é dentro dela. A pasta só é embrulho se não
    for, ela mesma, um pacote.

    Args:
        paths: Caminhos já normalizados, relativos à fonte.

    Returns:
        O prefixo a remover (com "/" final), ou "" quando não há embrulho.
    """
    top_segments = {path.split("/")[0] for path in paths}
    if len(top_segments) != 1:
        return ""

    root = top_segments.pop()

    # Raiz que é um pacote (ou um arquivo solto) não é embrulho
    if root.endswith(".py") or f"{root}/__init__.py" in paths:
        return ""

    # Todo caminho precisa estar dentro dela; senão a raiz é um arquivo de topo
    if not all(path.startswith(f"{root}/") for path in paths):
        return ""

    return f"{root}/"


def _walk_directory(root: Path) -> list[str]:
    """Percorre um diretório devolvendo os caminhos relativos dos arquivos.

    Poda as pastas que não são o Projeto-Alvo durante a descida, para não
    percorrer um `.venv` inteiro só para descartá-lo depois.

    Args:
        root: Raiz do Projeto-Alvo em disco.

    Returns:
        Caminhos dos arquivos, relativos a `root`, com separador "/".
    """
    paths = []

    for current, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in NON_PROJECT_FOLDERS]
        for name in filenames:
            paths.append(Path(current, name).relative_to(root).as_posix())

    return paths


def _read_directory_file(root: Path, path: str) -> str | None:
    """Lê um arquivo de um Projeto-Alvo em diretório, sem repercorrer a árvore.

    Args:
        root: Raiz do Projeto-Alvo em disco.
        path: Caminho relativo à raiz.

    Returns:
        Bytes decodificados do arquivo, ou None se o caminho não puder ser lido ou
        escapar da raiz do Projeto-Alvo.
    """
    clean = _normalize(path)

    if not clean or not _is_project_path(clean) or ".." in clean.split("/"):
        return None

    try:
        target = root / clean

        # `_normalize` tira a barra inicial, mas não a letra de unidade: em
        # `root / "C:/segredo.txt"` o pathlib descarta `root` e o caminho passa a
        # valer sozinho. Conferir a contenção depois de resolver é o que sustenta a
        # garantia documentada — nenhuma leitura fora da raiz do Projeto-Alvo.
        if not target.resolve().is_relative_to(root.resolve()):
            return None

        return _decode(target.read_bytes())
    except Exception:
        return None


def is_supported(source: object) -> bool:
    """Indica se a fonte é de uma espécie que o despacho sabe abrir.

    Quem valida o Projeto-Alvo precisa distinguir "esta fonte não tem arquivo .py"
    de "não sei abrir esta fonte": as duas produzem lista vazia de caminhos, mas só
    a primeira é um diagnóstico sobre o Projeto-Alvo. O `isinstance` segue confinado
    aqui (ADR-0006).

    Args:
        source: Candidata a fonte do Projeto-Alvo.

    Returns:
        True se for ZipFile, TarFile, Path ou dict.
    """
    return isinstance(source, (zipfile.ZipFile, tarfile.TarFile, Path, dict))


def _raw_paths(source: ProjectSource) -> list[str]:
    """Lista os caminhos crus dos arquivos de uma fonte, sem normalizar.

    Entradas de diretório não são arquivos e ficam de fora.

    Args:
        source: Fonte do Projeto-Alvo (ZipFile, TarFile, Path ou dict).

    Returns:
        Caminhos como a fonte os registra. Vazio se a espécie não for suportada.
    """
    if isinstance(source, zipfile.ZipFile):
        return [info.filename for info in source.infolist() if not info.is_dir()]

    if isinstance(source, tarfile.TarFile):
        return [member.name for member in source.getmembers() if member.isfile()]

    if isinstance(source, Path):
        return _walk_directory(source)

    if isinstance(source, dict):
        return list(source)

    return []


def _build_index(source: ProjectSource) -> dict[str, str]:
    """Mapeia cada caminho relativo à raiz do Projeto-Alvo ao caminho cru da fonte.

    É o que permite `read_text` receber um `str` do chamador e ainda assim achar o
    membro certo dentro do archive, inclusive quando há pasta-embrulho.

    Args:
        source: Fonte do Projeto-Alvo (ZipFile, TarFile, Path ou dict).

    Returns:
        Mapa caminho relativo à raiz -> caminho cru.
    """
    normalized: dict[str, str] = {}

    for raw in _raw_paths(source):
        clean = _normalize(raw)
        if clean and _is_project_path(clean):
            normalized[clean] = raw

    # O diretório apontado pelo usuário já é a raiz: nada a descascar.
    if isinstance(source, Path):
        return normalized

    prefix = _project_root_prefix(list(normalized))
    if not prefix:
        return normalized

    return {
        path[len(prefix) :]: raw
        for path, raw in normalized.items()
        if path.startswith(prefix)
    }


# Índice já montado de cada archive. Um archive é aberto sobre bytes em memória e não
# muda enquanto existe, então o índice vale por toda a sua vida; a entrada some quando
# o archive é coletado (um novo upload não acumula com o anterior).
_ARCHIVE_INDEX: WeakKeyDictionary = WeakKeyDictionary()


def _index(source: ProjectSource) -> dict[str, str]:
    """Índice da fonte, montado uma vez por archive.

    `read_text` é chamada uma vez por arquivo que passa pelo filtro. Sem memorizar,
    ler N arquivos de um archive custaria N varreduras do índice inteiro — o mesmo
    O(n²) que `_read_directory_file` já evita do lado do diretório.

    Args:
        source: Fonte do Projeto-Alvo (ZipFile, TarFile, Path ou dict).

    Returns:
        Mapa caminho relativo à raiz -> caminho cru.
    """
    if not isinstance(source, (zipfile.ZipFile, tarfile.TarFile)):
        return _build_index(source)

    cached = _ARCHIVE_INDEX.get(source)
    if cached is None:
        cached = _build_index(source)
        _ARCHIVE_INDEX[source] = cached

    return cached


def list_paths(source: ProjectSource) -> list[str]:
    """Lista os arquivos do Projeto-Alvo, relativos à sua raiz.

    A ordem é alfabética, e não a da fonte: um mesmo Projeto-Alvo precisa produzir
    o mesmo relatório vindo de diretório ou de archive, e a Origem de um pacote
    declarado duas vezes é a da primeira ocorrência.

    Args:
        source: Fonte do Projeto-Alvo (ZipFile, TarFile, Path ou dict).

    Returns:
        Caminhos com separador "/", relativos à raiz do Projeto-Alvo, ordenados.
        Vazio se a espécie de fonte não for suportada.
    """
    return sorted(_index(source))


def read_text(source: ProjectSource, path: str) -> str | None:
    """Lê como texto um arquivo do Projeto-Alvo, pelo caminho.

    Args:
        source: Fonte do Projeto-Alvo (ZipFile, TarFile, Path ou dict).
        path: Caminho relativo à raiz do Projeto-Alvo, como devolvido por
            `list_paths`.

    Returns:
        Conteúdo do arquivo, com bytes inválidos descartados, ou None se o caminho
        não existir na fonte ou não puder ser lido.
    """
    # Num diretório o caminho já é o caminho: resolver direto evita repercorrer a
    # árvore inteira a cada arquivo lido, que é o que `_index` custaria aqui.
    if isinstance(source, Path):
        return _read_directory_file(source, path)

    raw = _index(source).get(path)
    if raw is None:
        return None

    try:
        if isinstance(source, zipfile.ZipFile):
            data = source.read(raw)
        elif isinstance(source, tarfile.TarFile):
            extracted = source.extractfile(raw)
            if extracted is None:
                return None
            data = extracted.read()
        elif isinstance(source, dict):
            return source[raw]
        else:
            return None
    except Exception:
        return None

    return _decode(data)


def open_directory(path: str) -> tuple[Path | None, str]:
    """Abre um diretório local como fonte do Projeto-Alvo.

    Valida existência, tipo, permissão de leitura e a marca de projeto Python na
    raiz. A última é o que impede apontar para a pasta do usuário e esperar o
    Baita Auditor percorrer o disco inteiro antes de reclamar; a auditoria dos
    requisitos mínimos, essa sim completa, fica com `validate_project_structure`.

    Args:
        path: Caminho digitado pelo usuário.

    Returns:
        Par (fonte, erro). Com sucesso, o Path do diretório e "". Em falha, None e
        a mensagem a exibir — `core/` não conhece Streamlit, então quem chama é
        que decide como mostrá-la.
    """
    cleaned = path.strip().strip('"').strip("'")
    if not cleaned:
        return None, "❌ Informe o caminho do diretório do Projeto-Alvo."

    directory = Path(cleaned).expanduser()

    if not directory.exists():
        return None, f"❌ Caminho não encontrado: {directory}"

    if not directory.is_dir():
        return None, f"❌ O caminho informado não é um diretório: {directory}"

    try:
        is_project = _looks_like_a_python_project(directory)
    except PermissionError:
        return None, f"❌ Sem permissão de leitura em: {directory}"
    except OSError as error:
        return None, f"❌ Não foi possível ler o diretório: {error}"

    if not is_project:
        return None, (
            f"❌ O caminho não parece um projeto Python: {directory}\n"
            "Esperado, na raiz, um arquivo .py ou uma Declaração "
            "(pyproject.toml, requirements.txt, environment.yml)."
        )

    return directory, ""
