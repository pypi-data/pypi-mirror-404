import csv
from pathlib import Path

from qa_testing_utils.file_utils import *


def should_create_valid_csv(tmp_path: Path) -> None:
    # Prepare test data
    data: list[dict[str, object]] = [
        {"a": 1, "b": "x"},
        {"a": 2, "b": "y"},
        {"a": 3, "b": "z"},
    ]
    csv_path = tmp_path / "test.csv"

    # Call the function
    write_csv(csv_path, data)

    # Read back and check
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert rows == [
        {"a": "1", "b": "x"},
        {"a": "2", "b": "y"},
        {"a": "3", "b": "z"},
    ]


def should_write_empty_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "empty.csv"
    write_csv(csv_path, [])
    assert not csv_path.exists() or csv_path.read_text() == ""


def should_iterable_reader_reads_chunks():
    data = [b'abc', b'def', b'ghi']
    reader = IterableReader.from_(data)
    assert reader.read() == b'abcdefghi'
    reader.close()


def should_stream_file_reads_file(tmp_path: Path):
    file_path = tmp_path / "test.bin"
    file_path.write_bytes(b"1234567890")
    chunks = list(stream_file(file_path, chunk_size=4))
    assert chunks == [b"1234", b"5678", b"90"]


def should_read_lines_handles_split_lines():
    chunks = [b"hello ", b"world\nthis is", b" a test\nend"]
    lines = list(read_lines(chunks, encoding="utf-8", eol="\n"))
    assert lines == ["hello world", "this is a test", "end"]


def should_crc32_of_file(tmp_path: Path):
    file_path = tmp_path / "crc.bin"
    file_path.write_bytes(b"abc123")
    with file_path.open("rb") as f:
        crc = crc32_of(f)
    import zlib
    assert crc == zlib.crc32(b"abc123") & 0xFFFFFFFF


def should_decompress_xz_stream():
    import lzma
    original = [b"hello world"]
    compressed = [lzma.compress(original[0])]
    decompressed = list(decompress_xz_stream(compressed))
    assert b"".join(decompressed) == b"hello world"


def should_extract_files_from_tar():
    import io
    import tarfile

    # Create a tar archive in memory
    file_content = b"testdata"
    tar_bytes = io.BytesIO()
    with tarfile.open(fileobj=tar_bytes, mode="w") as tar:
        info = tarfile.TarInfo(name="file.txt")
        info.size = len(file_content)
        tar.addfile(info, io.BytesIO(file_content))
    tar_bytes.seek(0)
    # Split tar_bytes into chunks to simulate streaming
    tar_chunks = list(iter(lambda: tar_bytes.read(4), b""))
    # Extract files from tar stream
    files = list(extract_files_from_tar(tar_chunks))
    assert len(files) == 1
    tarinfo, data = files[0]
    assert tarinfo.name == "file.txt"
    assert data == file_content

# TODO: decompress_xz_stream and extract_files_from_tar require binary test data.
