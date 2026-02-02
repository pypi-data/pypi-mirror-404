"""
safe_radix32
Radix32 encode long integers with a safe alphabet.

:copyright: 2026 Nándor Mátravölgyi
:license: Apache2, see LICENSE for more details.
"""
import os

__author__ = "Nándor Mátravölgyi"
__copyright__ = "Copyright 2026 Nándor Mátravölgyi"
__author_email__ = "nandor.matra@gmail.com"
__version__ = "0.4.2"


if os.environ.get("SAFE_RADIX32_PUREPYTHON"):
    from .pure import (
        encode_safe_radix32 as encode,
        decode_safe_radix32 as decode,
        SAFE_RADIX32_ALPHABET as ALPHABET,
        SAFE_RADIX32_ALPHABET_RE as ALPHABET_RE,
        encode_safe_radix32_fixed_width as encode_fw,
    )
else:
    try:
        from ._cython import (
            encode_safe_radix32 as encode,
            decode_safe_radix32 as decode,
            SAFE_RADIX32_ALPHABET as ALPHABET,
            SAFE_RADIX32_ALPHABET_RE as ALPHABET_RE,
            encode_safe_radix32_fixed_width as encode_fw,
        )
    except ImportError:
        from .pure import (
            encode_safe_radix32 as encode,
            decode_safe_radix32 as decode,
            SAFE_RADIX32_ALPHABET as ALPHABET,
            SAFE_RADIX32_ALPHABET_RE as ALPHABET_RE,
            encode_safe_radix32_fixed_width as encode_fw,
        )
