"""
safe_radix32 implementation in python

:copyright: 2021 Nándor Mátravölgyi
:license: Apache2, see LICENSE for more details.
"""
import re

SAFE_BASE_BITS = 5
SAFE_MASK = (1 << SAFE_BASE_BITS) - 1
SAFE_MAP = "2346789BCFGJKLMPQVWZbcfgjkmpqvwz"
SAFE_MAP_SHIFTS = (60, 55, 50, 45, 40, 35, 30, 25, 20, 15, 10, 5, 0)
SAFE_MAP_SHIFTS_NUM = 13
TOP_SHIFT_MAX0 = (1 << (64 - SAFE_MAP_SHIFTS[0])) - 1
TOP_SHIFT_MAX1 = SAFE_MAP[TOP_SHIFT_MAX0].encode("ascii")[0]

DECODE_LIMIT_HELPER0 = 1 << 63
DECODE_LIMIT_HELPER1 = DECODE_LIMIT_HELPER0 - 1

SAFE_UNMAP = (
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, 1, 2, -1, 3, 4,
    5, 6, -1, -1, -1, -1, -1, -1, -1, -1, 7, 8, -1, -1, 9, 10, -1, -1, 11, 12,
    13, 14, -1, -1, 15, 16, -1, -1, -1, -1, 17, 18, -1, -1, 19, -1, -1, -1, -1,
    -1, -1, -1, 20, 21, -1, -1, 22, 23, -1, -1, 24, 25, -1, 26, -1, -1, 27, 28,
    -1, -1, -1, -1, 29, 30, -1, -1, 31, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
)

SAFE_RADIX32_ALPHABET = SAFE_MAP
SAFE_RADIX32_ALPHABET_RE = re.compile(r"^[" + SAFE_RADIX32_ALPHABET + "]+$", re.ASCII)


def encode_safe_radix32(v: int) -> str:
    """
    :raise TypeError if input arguments is incorrect type
    :raise OverflowError if value is not C long
    """
    if not isinstance(v, int):
        raise TypeError
    if v >= 2 ** 63 or v < -(2 ** 63):  # mirror overflow semantics of c-long
        raise OverflowError
    c_string = []
    shift_i = 0
    while shift_i < SAFE_MAP_SHIFTS_NUM - 1:
        char_v = (v >> SAFE_MAP_SHIFTS[shift_i]) & SAFE_MASK
        if char_v > 0:
            if shift_i == 0:
                char_v &= TOP_SHIFT_MAX0
            shift_i += 1
            c_string.append(SAFE_MAP[char_v])
            break
        shift_i += 1
    while shift_i < SAFE_MAP_SHIFTS_NUM:
        c_string.append(SAFE_MAP[(v >> SAFE_MAP_SHIFTS[shift_i]) & SAFE_MASK])
        shift_i += 1
    return "".join(c_string)


def decode_safe_radix32(v: str) -> int:
    """
    :raise TypeError if input arguments is incorrect type
    :raise UnicodeEncodeError if input contains invalid characters (encoding-related)
    :raise OverflowError if input contains invalid characters (alphabet-related) or value is not C long
    """
    if not isinstance(v, str):
        raise TypeError
    c_string = v.encode("ascii")
    if len(c_string) > SAFE_MAP_SHIFTS_NUM:
        raise OverflowError
    if len(c_string) == SAFE_MAP_SHIFTS_NUM and c_string[0] > TOP_SHIFT_MAX1:
        raise OverflowError
    u = 0
    i = 0
    while True:
        x = SAFE_UNMAP[c_string[i]]
        if x == -1:
            raise OverflowError
        u |= x
        i += 1
        if i >= len(c_string):
            break
        u <<= SAFE_BASE_BITS
    # mirror overflow semantics of c-long
    if u & DECODE_LIMIT_HELPER0:
        u = (u & DECODE_LIMIT_HELPER1) - DECODE_LIMIT_HELPER0
    return u


def encode_safe_radix32_fixed_width(v: int) -> str:
    """
    :raise TypeError if input arguments is incorrect type
    :raise OverflowError value is not C long
    """
    if not isinstance(v, int):
        raise TypeError
    if v >= 2 ** 63 or v < -(2 ** 63):  # mirror overflow semantics of c-long
        raise OverflowError
    return "".join(
        (
            SAFE_MAP[(v >> 60) & 15],
            SAFE_MAP[(v >> 55) & 31],
            SAFE_MAP[(v >> 50) & 31],
            SAFE_MAP[(v >> 45) & 31],
            SAFE_MAP[(v >> 40) & 31],
            SAFE_MAP[(v >> 35) & 31],
            SAFE_MAP[(v >> 30) & 31],
            SAFE_MAP[(v >> 25) & 31],
            SAFE_MAP[(v >> 20) & 31],
            SAFE_MAP[(v >> 15) & 31],
            SAFE_MAP[(v >> 10) & 31],
            SAFE_MAP[(v >> 5) & 31],
            SAFE_MAP[v & 31],
        )
    )
