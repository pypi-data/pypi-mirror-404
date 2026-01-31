# IMPORT
from kryptoon import __internal__ as _internal # type: ignore

# MAIN
class Blake3:
    def __init__(self, buffer: bytes | None = None) -> None:
        self.internal = _internal.BLAKE3() # type: ignore
        if buffer:
            self.internal.update(buffer) # type: ignore
        #
        self.buffer = buffer
        #
        return None
    #
    def copy(self) -> "Blake3":
        #
        return Blake3(self.buffer)
    #
    def update(self, buffer: bytes) -> None:
        self.internal.update(buffer) # type: ignore
        #
        return None
    #
    def digest(self) -> bytes:
        result = self.internal.digest() # type: ignore
        #
        return result # type: ignore
    #
    def hexdigest(self) -> str:
        result = self.internal.digest() # type: ignore
        #
        return result.hex() # type: ignore
    #
    def extend(self, length: int) -> bytes:
        result = self.internal.extend(length) # type: ignore
        #
        return result # type: ignore
    #
    def hexextend(self, length: int) -> str:
        result = self.internal.extend(length) # type: ignore
        #
        return result.hex() # type: ignore
    #
    def keyhash(self, buffer: bytes, key: bytes) -> bytes:
        result = self.internal.extend(buffer, key) # type: ignore
        #
        return result # type: ignore
    #
    def derivekey(self, context: bytes, key: bytes) -> bytes:
        result = self.internal.extend(context, key) # type: ignore
        #
        return result # type: ignore
    #
    def reset(self) -> None:
        self.internal.reset() # type: ignore
        #
        return None

class Ripemd128:
    def __init__(self, buffer: bytes | None = None) -> None:
        self.internal = _internal.RIPEMD128() # type: ignore
        if buffer:
            self.internal.update(buffer) # type: ignore
        #
        self.buffer = buffer
        #
        return None
    #
    def copy(self) -> "Ripemd128":
        return Ripemd128(self.buffer)
    #
    def update(self, buffer: bytes) -> None:
        self.internal.update(buffer) # type: ignore
        #
        return None
    #
    def digest(self) -> bytes:
        result = self.internal.digest() # type: ignore
        return result # type: ignore
    #
    def hexdigest(self) -> str:
        result = self.internal.digest() # type: ignore
        return result.hex() # type: ignore
    #
    def reset(self) -> None:
        self.internal.reset() # type: ignore
        #
        return None

class Ripemd160:
    def __init__(self, buffer: bytes | None = None) -> None:
        self.internal = _internal.RIPEMD160() # type: ignore
        if buffer:
            self.internal.update(buffer) # type: ignore
        #
        self.buffer = buffer
        #
        return None
    #
    def copy(self) -> "Ripemd160":
        return Ripemd160(self.buffer)
    #
    def update(self, buffer: bytes) -> None:
        self.internal.update(buffer) # type: ignore
        #
        return None
    #
    def digest(self) -> bytes:
        result = self.internal.digest() # type: ignore
        return result # type: ignore
    #
    def hexdigest(self) -> str:
        result = self.internal.digest() # type: ignore
        return result.hex() # type: ignore
    #
    def reset(self) -> None:
        self.internal.reset() # type: ignore
        #
        return None

class Ripemd256:
    def __init__(self, buffer: bytes | None = None) -> None:
        self.internal = _internal.RIPEMD256() # type: ignore
        if buffer:
            self.internal.update(buffer) # type: ignore
        #
        self.buffer = buffer
        #
        return None
    #
    def copy(self) -> "Ripemd256":
        return Ripemd256(self.buffer)
    #
    def update(self, buffer: bytes) -> None:
        self.internal.update(buffer) # type: ignore
        #
        return None
    #
    def digest(self) -> bytes:
        result = self.internal.digest() # type: ignore
        return result # type: ignore
    #
    def hexdigest(self) -> str:
        result = self.internal.digest() # type: ignore
        return result.hex() # type: ignore
    #
    def reset(self) -> None:
        self.internal.reset() # type: ignore
        #
        return None

class Ripemd320:
    def __init__(self, buffer: bytes | None = None) -> None:
        self.internal = _internal.RIPEMD320() # type: ignore
        if buffer:
            self.internal.update(buffer) # type: ignore
        #
        self.buffer = buffer
        #
        return None
    #
    def copy(self) -> "Ripemd320":
        return Ripemd320(self.buffer)
    #
    def update(self, buffer: bytes) -> None:
        self.internal.update(buffer) # type: ignore
        #
        return None
    #
    def digest(self) -> bytes:
        result = self.internal.digest() # type: ignore
        return result # type: ignore
    #
    def hexdigest(self) -> str:
        result = self.internal.digest() # type: ignore
        return result.hex() # type: ignore
    #
    def reset(self) -> None:
        self.internal.reset() # type: ignore
        #
        return None

class Keccak224:
    def __init__(self, buffer: bytes | None = None) -> None:
        self.internal = _internal.KECCAK224() # type: ignore
        if buffer:
            self.internal.update(buffer) # type: ignore
        #
        self.buffer = buffer
        #
        return None
    #
    def copy(self) -> "Keccak224":
        return Keccak224(self.buffer)
    #
    def update(self, buffer: bytes) -> None:
        self.internal.update(buffer) # type: ignore
        #
        return None
    #
    def digest(self) -> bytes:
        result = self.internal.digest() # type: ignore
        return result # type: ignore
    #
    def hexdigest(self) -> str:
        result = self.internal.digest() # type: ignore
        return result.hex() # type: ignore
    #
    def reset(self) -> None:
        self.internal.reset() # type: ignore
        #
        return None

class Keccak256:
    def __init__(self, buffer: bytes | None = None) -> None:
        self.internal = _internal.KECCAK256() # type: ignore
        if buffer:
            self.internal.update(buffer) # type: ignore
        #
        self.buffer = buffer
        #
        return None
    #
    def copy(self) -> "Keccak256":
        return Keccak256(self.buffer)
    #
    def update(self, buffer: bytes) -> None:
        self.internal.update(buffer) # type: ignore
        #
        return None
    #
    def digest(self) -> bytes:
        result = self.internal.digest() # type: ignore
        return result # type: ignore
    #
    def hexdigest(self) -> str:
        result = self.internal.digest() # type: ignore
        return result.hex() # type: ignore
    #
    def reset(self) -> None:
        self.internal.reset() # type: ignore
        #
        return None

class Keccak384:
    def __init__(self, buffer: bytes | None = None) -> None:
        self.internal = _internal.KECCAK384() # type: ignore
        if buffer:
            self.internal.update(buffer) # type: ignore
        #
        self.buffer = buffer
        #
        return None
    #
    def copy(self) -> "Keccak384":
        return Keccak384(self.buffer)
    #
    def update(self, buffer: bytes) -> None:
        self.internal.update(buffer) # type: ignore
        #
        return None
    #
    def digest(self) -> bytes:
        result = self.internal.digest() # type: ignore
        return result # type: ignore
    #
    def hexdigest(self) -> str:
        result = self.internal.digest() # type: ignore
        return result.hex() # type: ignore
    #
    def reset(self) -> None:
        self.internal.reset() # type: ignore
        #
        return None

class Keccak512:
    def __init__(self, buffer: bytes | None = None) -> None:
        self.internal = _internal.KECCAK512() # type: ignore
        if buffer:
            self.internal.update(buffer) # type: ignore
        #
        self.buffer = buffer
        #
        return None
    #
    def copy(self) -> "Keccak512":
        return Keccak512(self.buffer)
    #
    def update(self, buffer: bytes) -> None:
        self.internal.update(buffer) # type: ignore
        #
        return None
    #
    def digest(self) -> bytes:
        result = self.internal.digest() # type: ignore
        return result # type: ignore
    #
    def hexdigest(self) -> str:
        result = self.internal.digest() # type: ignore
        return result.hex() # type: ignore
    #
    def reset(self) -> None:
        self.internal.reset() # type: ignore
        #
        return None
