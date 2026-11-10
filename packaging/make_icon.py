"""Generate a simple cyan Y-Proxy .ico (no external deps)."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


def _png(size: int) -> bytes:
    # Solid teal circle-ish mark on dark slate — raw RGBA then PNG.
    raw = bytearray()
    cx = cy = (size - 1) / 2.0
    r0 = size * 0.38
    for y in range(size):
        raw.append(0)  # filter None
        for x in range(size):
            dx, dy = x - cx, y - cy
            d = (dx * dx + dy * dy) ** 0.5
            if d <= r0:
                # cyan accent
                raw.extend((45, 226, 230, 255))
            elif d <= r0 + size * 0.08:
                raw.extend((20, 70, 90, 255))
            else:
                raw.extend((20, 48, 68, 255))
    compressed = zlib.compress(bytes(raw), 9)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(
            ">I", zlib.crc32(tag + data) & 0xFFFFFFFF
        )

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", compressed) + chunk(
        b"IEND", b""
    )


def write_ico(path: Path, sizes=(16, 32, 48, 256)) -> None:
    images = [_png(s) for s in sizes]
    count = len(images)
    offset = 6 + 16 * count
    header = struct.pack("<HHH", 0, 1, count)
    entries = b""
    blobs = b""
    for size, data in zip(sizes, images):
        w = 0 if size >= 256 else size
        h = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(data), offset)
        blobs += data
        offset += len(data)
    path.write_bytes(header + entries + blobs)


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    ico = here / "y-proxy.ico"
    png = here / "y-proxy.png"
    write_ico(ico)
    png.write_bytes(_png(256))
    print(ico)
    print(png)
