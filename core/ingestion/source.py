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


def _raw_paths(source) -> list[str]:
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


def _index(source) -> dict[str, str]:
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


def list_paths(source) -> list[str]:
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


def read_text(source, path: str) -> str | None:
    """Lê como texto um arquivo do Projeto-Alvo, pelo caminho.

    Args:
        source: Fonte do Projeto-Alvo (ZipFile, TarFile, Path ou dict).
        path: Caminho relativo à raiz do Projeto-Alvo, como devolvido por
            `list_paths`.

    Returns:
        Conteúdo do arquivo, com bytes inválidos descartados, ou None se o caminho
        não existir na fonte ou não puder ser lido.
    """
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
        elif isinstance(source, Path):
            data = (source / raw).read_bytes()
        elif isinstance(source, dict):
            return source[raw]
        else:
            return None
    except Exception:
        return None

    # Fim de linha uniforme: o mesmo Projeto-Alvo lido de um diretório no Windows
    # traria "\r\n" onde o archive traz "\n", e o "\r" residual entraria no Nome de
    # Distribuição de uma Declaração lida linha a linha.
    text = data.decode("utf-8", errors="ignore")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def open_directory(path: str) -> tuple[Path | None, str]:
    """Abre um diretório local como fonte do Projeto-Alvo.

    Valida o que o sistema de arquivos sabe responder — existência, tipo e
    permissão de leitura. Se o diretório é ou não um projeto Python é pergunta
    para `validate_project_structure`.

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
        os.scandir(directory).close()
    except PermissionError:
        return None, f"❌ Sem permissão de leitura em: {directory}"
    except OSError as error:
        return None, f"❌ Não foi possível ler o diretório: {error}"

    return directory, ""
