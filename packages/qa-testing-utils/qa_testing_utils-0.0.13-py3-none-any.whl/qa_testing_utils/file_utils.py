# SPDX-FileCopyrightText: 2025 Adrian Herscu
#
# SPDX-License-Identifier: Apache-2.0

import csv
from io import DEFAULT_BUFFER_SIZE, BufferedReader, RawIOBase
from lzma import LZMADecompressor
from pathlib import Path
from tarfile import TarInfo, open
from typing import BinaryIO, Iterable, Iterator, Tuple, final, override
from zlib import crc32

from more_itertools import peekable
from qa_testing_utils.logger import *
from qa_testing_utils.object_utils import *
from qa_testing_utils.string_utils import DOT, EMPTY_BYTES, SPACE, UTF_8

LAUNCHING_DIR: Final[Path] = Path.cwd()


@final
class IterableReader(RawIOBase, LoggerMixin, ImmutableMixin):
    """
    I/O read-only stream over iterable of bytes, enabling streaming mode.
    """

    def __init__(self, chunks: Iterable[bytes]):
        self._chunks = iter(chunks)
        self._accumulated_buffer = bytearray()

    @override
    def readable(self) -> bool:
        return True

    @override
    def readinto(self, output_buffer: memoryview) -> int:  # type: ignore
        # consume chunks, accumulating their bytes up to size of output buffer
        while len(self._accumulated_buffer) < len(output_buffer) \
                and (chunk := next(self._chunks, None)) is not None:
            self.log.debug(f"buffered chunk with length={len(chunk)}")
            self._accumulated_buffer.extend(chunk)

        # consume accumulated bytes up to size of output buffer
        consumed_bytes = min(len(self._accumulated_buffer), len(output_buffer))
        output_buffer[:consumed_bytes] = self._accumulated_buffer[:consumed_bytes]

        # delete consumed bytes, shifting left the accumulated buffer
        del self._accumulated_buffer[:consumed_bytes]

        self.log.debug(f"consumed {consumed_bytes} bytes")
        return consumed_bytes

    @staticmethod
    def from_(
            chunks: Iterable[bytes],
            buffer_size: int = DEFAULT_BUFFER_SIZE) -> BinaryIO:
        """
        Converts a stream of binary chunks into a BufferedReader.

        You should ensure closing.

        Args:
            chunks (Iterable[bytes]): stream of binary chunks

        Returns:
            io.BufferedReader: buffered reader around stream of binary chunks.
        """
        return BufferedReader(IterableReader(chunks), buffer_size)


# TODO perhaps there should be a writable stream to iterator utility too...


def stream_file(
        file_path: Path,
        chunk_size: int = DEFAULT_BUFFER_SIZE) -> Iterator[bytes]:
    """
    Streams a binary file from disk into an iterator.

    If the iterator is not consumed, the file will be closed when the iterator
    will be garbage collected.

    Args:
        file_path (Path): path to file
        chunk_size (int, optional): the chunk size. Defaults to 8192.

    Yields:
        Iterator[bytes]: the binary chunks stream
    """
    with file_path.open('rb') as f:
        yield from iter(lambda: f.read(chunk_size), EMPTY_BYTES)


def read_lines(
        byte_stream: Iterable[bytes],
        encoding: str = UTF_8,
        eol: str = LF) -> Iterator[str]:
    """
    Converts a stream of binary chunks into stream of text lines.
    Handles cases where lines are split across chunks.

    Args:
        byte_stream (Iterable[bytes]): the binary (chunks) stream
        encoding (str, optional): expected text encoding. Defaults to 'utf-8'.
        eol (str, optional): expected line-ending. Default to LF.

    Yields:
        Iterator[str]: stream of text lines, not terminated by EOL marker
    """
    has_content = False
    buffer = bytearray()
    eol_bytes = eol.encode(encoding)

    for chunk in byte_stream:
        print(DOT, end=SPACE)
        has_content = True
        buffer.extend(chunk)
        *lines, buffer = buffer.split(eol_bytes)  # keep partial line in buffer
        trace(f"streaming {len(lines)} lines; leftover {len(buffer)} chars")
        yield from (line.decode(encoding) for line in lines)

    if buffer:  # yield the leftover
        yield buffer.decode(encoding)

    if not has_content:
        trace("no lines")


def decompress_xz_stream(compressed_chunks: Iterable[bytes]) -> Iterator[bytes]:
    """
    Decompresses XZ stream.

    Args:
        compressed_chunks (Iterable[bytes]): stream of binary compressed chunks

    Yields:
        Iterator[bytes]: the decompressed stream
    """
    decompressor = LZMADecompressor()
    return map(decompressor.decompress, compressed_chunks)


def extract_files_from_tar(tar_chunks: Iterable[bytes]) -> Iterator[Tuple[TarInfo, bytes]]:
    """
    Extracts files from decompressed TAR stream.

    Args:
        tar_chunks (Iterable[bytes]): stream of decompressed TAR chunks

    Yields:
        Iterator[Tuple[tarfile.TarInfo, bytes]]: \
            streams tuples of meta-data and data for each file
    """
    with open(fileobj=IterableReader.from_(tar_chunks),
              mode='r|*') as tar:
        for member in tar:
            if member.isfile():
                extracted_file = tar.extractfile(member)
                if extracted_file:
                    yield member, extracted_file.read()


def crc32_of(file: BinaryIO, chunk_size: int = DEFAULT_BUFFER_SIZE) -> int:
    """
    Calculate the CRC of a binary stream from its current position to its tail,
    using chunked reading.

    Args:
        file (BinaryIO): The file object to read data from, starting from its current position.
        chunk_size (int): The size of chunks to read at a time (default is 8192).

    Returns:
        int: Calculated CRC value of the remaining file content.
    """
    crc_value = 0

    while chunk := file.read(chunk_size):
        crc_value = crc32(chunk, crc_value)

    return crc_value & 0xFFFFFFFF  # ensure 32-bit unsigned


def write_csv(file_path: Path, data_stream: Iterable[dict[str, object]]):
    """
    Writes a stream of flattened telemetry packets to a CSV file.

    Args:
        file_path: Path to the CSV file to be written.
        data_stream: Iterable of dictionaries representing the rows to be written.
    """
    stream = peekable(data_stream)  # Allow peeking to extract headers
    try:
        first_row: dict[str, object] = stream.peek()
    except StopIteration:
        # No data to write
        return
    with file_path.open(mode="w", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file, fieldnames=list(first_row.keys()))
        writer.writeheader()
        writer.writerows(stream)
