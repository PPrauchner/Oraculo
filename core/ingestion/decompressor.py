"""
Reading of compressed archive files (.zip).

Provides functions to open, list and access files inside a
ZIP archive, without needing to extract them to disk.

Input:
- ZIP archive as bytes

Output:
- Manipulable ZIP object (zip_ref)
- List of files contained in the ZIP
- Contents of specific files
"""

import io
import zipfile
import tarfile
from utils.functions import registrar, EXTRATORES


@registrar(EXTRATORES, "zip")
def read_zip_file(file_bytes: bytes) -> zipfile.ZipFile:
    """
    Reads a ZIP archive from bytes and returns a manipulable object.

    Args:
        file_bytes (bytes): The ZIP archive contents as bytes.

    Returns:
        zipfile.ZipFile: An object representing the ZIP archive, allowing
                         access to the files contained in it.
    """

    try:
        zip_ref = zipfile.ZipFile(io.BytesIO(file_bytes))
        return zip_ref
    except zipfile.BadZipFile:
        print("The uploaded file is not a valid ZIP.")
        return None


@registrar(EXTRATORES, "tar")
def tar_file(file_bytes: bytes) -> tarfile.TarFile:
    """
    Reads a TAR archive from bytes and returns a manipulable object.

    Args:
        file_bytes (bytes): The TAR archive contents as bytes.

    Returns:
        tarfile.TarFile: An object representing the TAR archive, allowing
                         access to the files contained in it.
    """

    try:
        tar_ref = tarfile.open(fileobj=io.BytesIO(file_bytes))
        return tar_ref
    except tarfile.TarError:
        print("The uploaded file is not a valid TAR.")
        return None


@registrar(EXTRATORES, "tar.gz")
def tar_gz_file(file_bytes: bytes) -> tarfile.TarFile:
    """
    Reads a TAR.GZ archive from bytes and returns a manipulable object.

    Args:
        file_bytes (bytes): The TAR.GZ archive contents as bytes.

    Returns:
        tarfile.TarFile: An object representing the TAR.GZ archive, allowing
                         access to the files contained in it.
    """

    try:
        tar_ref = tarfile.open(fileobj=io.BytesIO(file_bytes), mode="r:gz")
        return tar_ref
    except tarfile.TarError:
        print("The uploaded file is not a valid TAR.GZ.")
        return None


def get_archive_files(archive: zipfile.ZipFile) -> list:
    """Gets the list of files contained in a ZIP or TAR archive.
    Args:
        archive (zipfile.ZipFile or tarfile.TarFile): The compressed archive object.
    Returns:
        list: A list of files contained in the compressed archive.
    """
    if isinstance(archive, zipfile.ZipFile):
        return archive.filelist
    elif isinstance(archive, tarfile.TarFile):
        return archive.getmembers()
    return []


def process_uploaded_file(uploaded_file):
    """Function responsible for

    """
    if not uploaded_file:
        return None

    file_name = uploaded_file.name.lower()

    for key, value in EXTRATORES.items():
        if file_name.endswith(f".{key}"):
            return value(uploaded_file.read())

    return None
