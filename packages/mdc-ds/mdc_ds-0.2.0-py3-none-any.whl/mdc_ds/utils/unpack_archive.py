import gzip
import tarfile
import zipfile
from pathlib import Path


def unpack_archive(filepath: Path | str, output: Path | str) -> Path:
    filepath = Path(filepath)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if filepath.is_file():
        try:
            with tarfile.open(filepath, "r:gz") as tar:
                tar.extractall(output, filter="data")
        except (tarfile.ReadError, gzip.BadGzipFile):
            try:
                with zipfile.ZipFile(filepath, "r") as zf:
                    zf.extractall(output)
            except zipfile.BadZipFile:
                raise ValueError(f"Invalid file format: {filepath}")
        except Exception as e:
            raise ValueError(f"Error unpacking archive: {e}")
    else:
        raise ValueError(f"Invalid file path: {filepath}")
    return output
