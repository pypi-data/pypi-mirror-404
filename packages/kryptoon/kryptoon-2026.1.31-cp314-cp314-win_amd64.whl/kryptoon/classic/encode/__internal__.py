# IMPORT
from kryptoon import __internal__ as _internal # type: ignore

# MAIN
def b58encode(buffer: bytes) -> bytes:
    result = _internal.b58encode(buffer) #type: ignore
    return result # type: ignore

def b58decode(buffer: bytes) -> bytes:
    result = _internal.b58decode(buffer) #type: ignore
    return result # type: ignore
