import os

from safe_radix32.bytes import encode_safe_radix32_bytes, decode_safe_radix32_bytes


def test_safe_radix32_bytes():
    # test translation integrity with some patterns
    for length in range(1, 40):
        for start in range(256):
            for step in [1, 2, 34, 8, 13, 21, 31, 32, 55]:
                v = b"".join([((i * step + start) % 256).to_bytes(1, "big") for i in range(length)])
                e = encode_safe_radix32_bytes(v)
                assert decode_safe_radix32_bytes(e) == v, f"{v}\n{e}"
        for _ in range(1000):
            v = os.urandom(length)
            e = encode_safe_radix32_bytes(v)
            assert decode_safe_radix32_bytes(e) == v, f"{v}\n{e}"

    rb = b"\x01\x00+\xdcTb\x91\xf4\xb1'\x10\xd5~\x15\xce\n\x05V\x07@M_\xb4\xf9\x8b"
    e = encode_safe_radix32_bytes(rb)
    assert e == "2724gg4bKGCzFKFB46Ggq8MM3C4cK3m2FcPpFwKJ"
    assert decode_safe_radix32_bytes(e) == rb
