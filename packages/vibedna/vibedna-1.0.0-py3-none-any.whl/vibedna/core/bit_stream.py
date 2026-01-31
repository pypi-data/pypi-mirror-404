"""
VibeDNA Bit Stream Utilities

Binary stream utilities for efficient handling of bit-level operations
during DNA encoding and decoding.

© 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
"""

from typing import Iterator, Optional, Union, List
from io import BytesIO


class BitStream:
    """
    Efficient bit-level stream for DNA encoding operations.

    Provides methods for reading and writing individual bits,
    bit groups, and converting between bytes and bits.

    Example:
        >>> stream = BitStream(b"Hello")
        >>> stream.read_bits(2)  # Read 2 bits
        '01'
        >>> stream.read_bits(8)  # Read 8 bits (1 byte)
        '001001000'

        >>> writer = BitStream()
        >>> writer.write_bits('01001000')  # 'H'
        >>> writer.write_bits('01100101')  # 'e'
        >>> writer.to_bytes()
        b'He'
    """

    def __init__(self, data: Optional[Union[bytes, str]] = None):
        """
        Initialize bit stream.

        Args:
            data: Optional initial data (bytes or binary string)
        """
        self._buffer: List[str] = []
        self._position = 0

        if data is not None:
            if isinstance(data, bytes):
                self._buffer = list(self._bytes_to_bits(data))
            elif isinstance(data, str):
                # Assume binary string
                self._buffer = list(data)

    @property
    def position(self) -> int:
        """Current read position in bits."""
        return self._position

    @property
    def length(self) -> int:
        """Total length in bits."""
        return len(self._buffer)

    @property
    def remaining(self) -> int:
        """Remaining bits to read."""
        return max(0, len(self._buffer) - self._position)

    def read_bit(self) -> Optional[str]:
        """
        Read a single bit.

        Returns:
            '0' or '1', or None if at end of stream
        """
        if self._position >= len(self._buffer):
            return None

        bit = self._buffer[self._position]
        self._position += 1
        return bit

    def read_bits(self, count: int) -> str:
        """
        Read multiple bits.

        Args:
            count: Number of bits to read

        Returns:
            Binary string of requested bits (may be shorter if at end)
        """
        end = min(self._position + count, len(self._buffer))
        bits = "".join(self._buffer[self._position:end])
        self._position = end
        return bits

    def read_byte(self) -> Optional[int]:
        """
        Read 8 bits as a byte.

        Returns:
            Integer value 0-255, or None if insufficient bits
        """
        bits = self.read_bits(8)
        if len(bits) < 8:
            return None
        return int(bits, 2)

    def read_bytes(self, count: int) -> bytes:
        """
        Read multiple bytes.

        Args:
            count: Number of bytes to read

        Returns:
            Bytes object (may be shorter if at end)
        """
        result = []
        for _ in range(count):
            byte = self.read_byte()
            if byte is None:
                break
            result.append(byte)
        return bytes(result)

    def write_bit(self, bit: str) -> None:
        """
        Write a single bit.

        Args:
            bit: '0' or '1'
        """
        if bit not in ("0", "1"):
            raise ValueError(f"Invalid bit value: {bit}")
        self._buffer.append(bit)

    def write_bits(self, bits: str) -> None:
        """
        Write multiple bits.

        Args:
            bits: Binary string of bits
        """
        for bit in bits:
            self.write_bit(bit)

    def write_byte(self, value: int) -> None:
        """
        Write a byte as 8 bits.

        Args:
            value: Integer value 0-255
        """
        if not 0 <= value <= 255:
            raise ValueError(f"Byte value out of range: {value}")
        self.write_bits(format(value, "08b"))

    def write_bytes(self, data: bytes) -> None:
        """
        Write multiple bytes.

        Args:
            data: Bytes to write
        """
        for byte in data:
            self.write_byte(byte)

    def write_int(self, value: int, bits: int) -> None:
        """
        Write an integer using specified number of bits.

        Args:
            value: Integer value to write
            bits: Number of bits to use
        """
        max_value = (1 << bits) - 1
        if value < 0 or value > max_value:
            raise ValueError(f"Value {value} doesn't fit in {bits} bits")
        self.write_bits(format(value, f"0{bits}b"))

    def seek(self, position: int) -> None:
        """
        Move read position.

        Args:
            position: New position in bits
        """
        if position < 0:
            position = len(self._buffer) + position
        self._position = max(0, min(position, len(self._buffer)))

    def reset(self) -> None:
        """Reset read position to beginning."""
        self._position = 0

    def clear(self) -> None:
        """Clear all data."""
        self._buffer = []
        self._position = 0

    def to_binary(self) -> str:
        """
        Get all data as binary string.

        Returns:
            Binary string representation
        """
        return "".join(self._buffer)

    def to_bytes(self) -> bytes:
        """
        Convert to bytes.

        Pads with zeros if not byte-aligned.

        Returns:
            Bytes representation
        """
        binary = self.to_binary()

        # Pad to byte boundary
        padding = (8 - len(binary) % 8) % 8
        binary += "0" * padding

        return bytes(int(binary[i:i + 8], 2) for i in range(0, len(binary), 8))

    def iter_bits(self, count: int = 2) -> Iterator[str]:
        """
        Iterate over bits in groups.

        Args:
            count: Number of bits per group

        Yields:
            Binary strings of specified length
        """
        while self.remaining >= count:
            yield self.read_bits(count)

        # Handle remaining bits if any
        if self.remaining > 0:
            yield self.read_bits(self.remaining)

    def iter_bytes(self) -> Iterator[int]:
        """
        Iterate over bytes.

        Yields:
            Integer values 0-255
        """
        while self.remaining >= 8:
            byte = self.read_byte()
            if byte is not None:
                yield byte

    def pad_to_alignment(self, alignment: int = 8) -> int:
        """
        Pad with zeros to specified alignment.

        Args:
            alignment: Bit alignment (default 8 for byte alignment)

        Returns:
            Number of padding bits added
        """
        current_length = len(self._buffer)
        padding = (alignment - current_length % alignment) % alignment

        for _ in range(padding):
            self._buffer.append("0")

        return padding

    @staticmethod
    def _bytes_to_bits(data: bytes) -> str:
        """Convert bytes to binary string."""
        return "".join(format(byte, "08b") for byte in data)

    @staticmethod
    def from_int(value: int, bits: int) -> "BitStream":
        """
        Create BitStream from integer.

        Args:
            value: Integer value
            bits: Number of bits to use

        Returns:
            New BitStream instance
        """
        stream = BitStream()
        stream.write_int(value, bits)
        return stream

    @staticmethod
    def from_file(path: str) -> "BitStream":
        """
        Create BitStream from file.

        Args:
            path: File path

        Returns:
            New BitStream instance with file contents
        """
        with open(path, "rb") as f:
            return BitStream(f.read())

    def __len__(self) -> int:
        """Return length in bits."""
        return len(self._buffer)

    def __repr__(self) -> str:
        """String representation."""
        return f"BitStream(length={len(self._buffer)}, position={self._position})"


class BitWriter:
    """
    Efficient bit writer for building binary data.

    Optimized for sequential writing operations.
    """

    def __init__(self):
        self._bytes = BytesIO()
        self._current_byte = 0
        self._bit_position = 0

    def write_bit(self, bit: int) -> None:
        """Write a single bit (0 or 1)."""
        self._current_byte = (self._current_byte << 1) | (bit & 1)
        self._bit_position += 1

        if self._bit_position == 8:
            self._bytes.write(bytes([self._current_byte]))
            self._current_byte = 0
            self._bit_position = 0

    def write_bits(self, value: int, count: int) -> None:
        """Write multiple bits from an integer."""
        for i in range(count - 1, -1, -1):
            self.write_bit((value >> i) & 1)

    def flush(self) -> bytes:
        """Flush remaining bits and return all data."""
        if self._bit_position > 0:
            # Pad remaining bits with zeros
            self._current_byte <<= (8 - self._bit_position)
            self._bytes.write(bytes([self._current_byte]))
            self._current_byte = 0
            self._bit_position = 0

        return self._bytes.getvalue()


class BitReader:
    """
    Efficient bit reader for parsing binary data.

    Optimized for sequential reading operations.
    """

    def __init__(self, data: bytes):
        self._data = data
        self._byte_position = 0
        self._bit_position = 0

    def read_bit(self) -> Optional[int]:
        """Read a single bit."""
        if self._byte_position >= len(self._data):
            return None

        byte = self._data[self._byte_position]
        bit = (byte >> (7 - self._bit_position)) & 1

        self._bit_position += 1
        if self._bit_position == 8:
            self._bit_position = 0
            self._byte_position += 1

        return bit

    def read_bits(self, count: int) -> Optional[int]:
        """Read multiple bits as an integer."""
        result = 0
        for _ in range(count):
            bit = self.read_bit()
            if bit is None:
                return None
            result = (result << 1) | bit
        return result

    @property
    def remaining_bits(self) -> int:
        """Number of remaining bits."""
        remaining_bytes = len(self._data) - self._byte_position
        return remaining_bytes * 8 - self._bit_position


# © 2026 VibeDNA powered by VibeCaaS.com a division of NeuralQuantum.ai LLC. All rights reserved.
