from io import StringIO, BytesIO

from safe_radix32.pure import SAFE_MAP, SAFE_BASE_BITS

DECODE_UNPAD = {1: 4, 3: 3, 4: 2, 6: 1}
DECODE_REVERSE_MAP = {v: k for k, v in enumerate(SAFE_MAP.encode())}
ENCODE_DOUBLED_MAP = [a + b for a in SAFE_MAP for b in SAFE_MAP]


def encode_safe_radix32_bytes(b: bytes) -> str:
    leftover = len(b) % 5
    buffer = StringIO()
    _fb = int.from_bytes
    for i in range(0, len(b) - leftover, 5):
        v = _fb(b[i : i + 5], "big")
        buffer.write(
            "".join(
                (
                    ENCODE_DOUBLED_MAP[v >> 30],
                    ENCODE_DOUBLED_MAP[(v >> 20) & 1023],
                    ENCODE_DOUBLED_MAP[(v >> 10) & 1023],
                    ENCODE_DOUBLED_MAP[v & 1023],
                )
            )
        )
    if leftover:
        pad = 5 - leftover
        v = _fb(b[-leftover:] + b"\x00" * pad, "big")
        buffer.write(ENCODE_DOUBLED_MAP[v >> 30])  # 10 : 1
        if pad < 4:
            buffer.write(ENCODE_DOUBLED_MAP[(v >> 20) & 1023])  # 20 : 2
        if pad < 3:
            buffer.write(SAFE_MAP[(v >> 15) & 31])  # 25 : 3
        if pad < 2:
            buffer.write(ENCODE_DOUBLED_MAP[(v >> 5) & 1023])  # 35 : 4
        # buffer.append(SAFE_MAP[v & 31])
    return buffer.getvalue()


def decode_safe_radix32_bytes(s: str) -> bytes:
    s = s.encode("ascii")
    leftover = len(s) % 8
    buffer = BytesIO()
    try:
        for o in range(0, len(s) - leftover, 8):
            u = 0
            for c in s[o : o + 8]:
                u = (u << SAFE_BASE_BITS) + DECODE_REVERSE_MAP[c]
            buffer.write(u.to_bytes(5, "big"))
        if leftover:
            pad = 8 - leftover
            s = s[-leftover:] + b"2" * pad
            u = 0
            for c in s:
                u = (u << SAFE_BASE_BITS) + DECODE_REVERSE_MAP[c]
            b = u.to_bytes(5, "big")
            buffer.write(b[: DECODE_UNPAD[pad]])
    except KeyError:
        raise OverflowError
    return buffer.getvalue()
