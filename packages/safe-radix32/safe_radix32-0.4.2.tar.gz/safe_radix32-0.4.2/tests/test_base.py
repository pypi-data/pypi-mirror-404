import random

import pytest

import safe_radix32


def _to_fixed_width(t: str) -> str:
    return safe_radix32.ALPHABET[0] * (13 - len(t)) + t


def test_safe_radix32_base():
    assert len(safe_radix32.encode_fw(0)) == 13
    assert safe_radix32.ALPHABET == "2346789BCFGJKLMPQVWZbcfgjkmpqvwz"
    for i in range(32):
        t = safe_radix32.encode(i)
        assert t == safe_radix32.ALPHABET[i]
        assert safe_radix32.ALPHABET_RE.match(t) is not None
        assert safe_radix32.decode(t) == i
    for i, t in [
        (2 ** 32 - 1, "6zzzzzz"),
        (2 ** 32, "7222222"),
        (2 ** 48 - 1, "Bzzzzzzzzz"),
        (2 ** 48, "C222222222"),
        (2 ** 60 - 1, "zzzzzzzzzzzz"),
        (2 ** 61 - 1, "3zzzzzzzzzzzz"),
        (2 ** 62 - 1, "6zzzzzzzzzzzz"),
        (2 ** 63 - 1, "Bzzzzzzzzzzzz"),
        (-(2 ** 32) + 1, "Pzzzzzq222223"),
        (-(2 ** 32), "Pzzzzzq222222"),
        (-(2 ** 62), "K222222222222"),
        (-(2 ** 63), "C222222222222"),
        (-(2 ** 63) + 1, "C222222222223"),
        (int("01" * 32, 2), "8GcGcGcGcGcGc"),
        (int("10" * 31, 2), "4cGcGcGcGcGcG"),
        (int("0110" * 16, 2), "9KkZ9KkZ9KkZ9"),
        (int("0011" * 16, 2), "69KkZ9KkZ9KkZ"),
        (int("100" + "1100" * 15, 2), "7kZ9KkZ9KkZ9K"),
        (8474785761110355227, "BJB6qgwJCGpCp"),
        (3927410648750184479, "6L2Bg8bwvMf2z"),
    ]:
        t_fw = _to_fixed_width(t)
        assert safe_radix32.encode(i) == t, t
        assert safe_radix32.encode_fw(i) == t_fw, f"{i} {t_fw}"
        assert safe_radix32.decode(t) == i, t
        assert safe_radix32.ALPHABET_RE.match(t) is not None
    # random consistency checks
    for _ in range(5000):
        r = random.randint(-(2 ** 63), 2 ** 63 - 1)
        x = safe_radix32.encode(r)
        x_fw = _to_fixed_width(x)
        assert safe_radix32.encode_fw(r) == x_fw
        assert safe_radix32.decode(x) == r, x
        assert safe_radix32.ALPHABET_RE.match(x) is not None


def test_safe_radix32_limits():
    with pytest.raises(OverflowError):
        safe_radix32.encode(2 ** 63)
    with pytest.raises(OverflowError):
        safe_radix32.encode_fw(2 ** 63)
    with pytest.raises(OverflowError):
        safe_radix32.encode(-(2 ** 63) - 1)
    with pytest.raises(OverflowError):
        safe_radix32.encode_fw(-(2 ** 63) - 1)
    for c in "01AaEIoOyYxXrR/*_:?#&%!+'\"":
        with pytest.raises(OverflowError):
            safe_radix32.decode(c)
    for c in "\xffáŐ":
        with pytest.raises(UnicodeEncodeError):
            safe_radix32.decode(c)
    assert safe_radix32.decode("222") == 0
    assert safe_radix32.decode("2222222222222") == 0
    assert safe_radix32.decode("7777") == 135300
    assert safe_radix32.decode("7777777777777") == 4760450083537948804
    assert safe_radix32.decode("3777777777777") == 1301685569717407876
    assert safe_radix32.decode("zzzzzzzzzzzz") == 1152921504606846975
    assert safe_radix32.decode("Pzzzzzzzzzzzz") == -1
    for v in ["88888888888888", "48888888888888", "Qzzzzzzzzzzzz", "zzzzzzzzzzzzz"]:
        with pytest.raises(OverflowError):
            safe_radix32.decode(v)


def test_safe_radix32_types():
    for v in [None, ["88"], 5451]:
        with pytest.raises(TypeError):
            safe_radix32.decode(v)
    for v in [None, ["88"], "8888"]:
        with pytest.raises(TypeError):
            safe_radix32.encode(v)
        with pytest.raises(TypeError):
            safe_radix32.encode_fw(v)
