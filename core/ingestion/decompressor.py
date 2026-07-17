"""
Módulo responsável pela leitura de arquivos compactados (.zip).

Fornece funções para abrir, listar e acessar arquivos dentro de um
arquivo ZIP, sem necessidade de extração para o disco.

Entrada:
- Arquivo ZIP em formato de bytes

Saída:
- Objeto manipulável do ZIP (zip_ref)
- Lista de arquivos contidos no ZIP
- Conteúdo de arquivos específicos
"""

import io
import zipfile
import tarfile
from utils.functions import registrar, EXTRATORES


@registrar(EXTRATORES, "zip")
def read_zip_file(file_bytes: bytes) -> zipfile.ZipFile:
    """
    Lê um arquivo ZIP a partir de bytes e retorna um objeto manipulável.

    Args:
        file_bytes (bytes): O conteúdo do arquivo ZIP em formato de bytes.

    Returns:
        zipfile.ZipFile: Um objeto que representa o arquivo ZIP, permitindo
                         acesso aos arquivos contidos nele.
    """

    try:
        zip_ref = zipfile.ZipFile(io.BytesIO(file_bytes))
        return zip_ref
    except zipfile.BadZipFile:
        print("O arquivo enviado não é um ZIP válido.")
        return None


@registrar(EXTRATORES, "tar")
def tar_file(file_bytes: bytes) -> tarfile.TarFile:
    """
    Lê um arquivo TAR a partir de bytes e retorna um objeto manipulável.

    Args:
        file_bytes (bytes): O conteúdo do arquivo TAR em formato de bytes.

    Returns:
        tarfile.TarFile: Um objeto que representa o arquivo TAR, permitindo
                         acesso aos arquivos contidos nele.
    """

    try:
        tar_ref = tarfile.open(fileobj=io.BytesIO(file_bytes))
        return tar_ref
    except tarfile.TarError:
        print("O arquivo enviado não é um TAR válido.")
        return None


@registrar(EXTRATORES, "tar.gz")
def tar_gz_file(file_bytes: bytes) -> tarfile.TarFile:
    """
    Lê um arquivo TAR.GZ a partir de bytes e retorna um objeto manipulável.

    Args:
        file_bytes (bytes): O conteúdo do arquivo TAR.GZ em formato de bytes.

    Returns:
        tarfile.TarFile: Um objeto que representa o arquivo TAR.GZ, permitindo
                         acesso aos arquivos contidos nele.
    """

    try:
        tar_ref = tarfile.open(fileobj=io.BytesIO(file_bytes), mode="r:gz")
        return tar_ref
    except tarfile.TarError:
        print("O arquivo enviado não é um TAR.GZ válido.")
        return None


def get_archive_files(archive: zipfile.ZipFile) -> list:
    """Obtém a lista de arquivos contidos em um arquivo ZIP ou TAR.
    Args:
        archive (zipfile.ZipFile or tarfile.TarFile): O objeto do arquivo compactado.
    Returns:
        list: Uma lista de arquivos contidos no arquivo compactado.
    """
    if isinstance(archive, zipfile.ZipFile):
        return archive.filelist
    elif isinstance(archive, tarfile.TarFile):
        return archive.getmembers()
    return []


def process_uploaded_file(uploaded_file):
    """Função responsável por 
    
    """
    if not uploaded_file:
        return None

    file_name = uploaded_file.name.lower()

    for key, value in EXTRATORES.items():
        if file_name.endswith(f".{key}"):
            return value(uploaded_file.read())

    return None
