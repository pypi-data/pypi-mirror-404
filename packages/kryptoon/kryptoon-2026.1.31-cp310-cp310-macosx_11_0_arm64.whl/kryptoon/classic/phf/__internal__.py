# IMPORT
from kryptoon import __internal__ as _internal # type: ignore
import enum as _enum

# MAIN
class Algorithm:
    class Argon2(_enum.Enum):
        I = "i"
        D = "d"
        ID = "id"

class Argon2:
    def __init__(
            self,
            algorithm: Algorithm.Argon2 = Algorithm.Argon2.ID,
            *,
            version: int = 19,
            timecost: int = 3,
            memorycost: int = 65536,
            parallelism: int = 4,
            hashlen: int = 32,
            saltlen: int = 16
        ) -> None:
        self.algorithm = algorithm
        #
        match version:
            case 19:
                self.version = "0x13"
            case 16:
                self.version = "0x10"
            case _:
                raise ValueError("Version can be only 16 or 19")
        self.timecost = timecost
        self.memorycost = memorycost
        self.parallelism = parallelism
        self.hashlen = hashlen
        self.saltlen = saltlen
        #
        return None
    #
    def hash(self, password: bytes) -> bytes:
        result = _internal.argontwohash(  # type: ignore
            Algorithm.Argon2(self.algorithm).value,
            self.version,
            password.decode(),
            self.timecost,
            self.memorycost,
            self.parallelism,
            self.hashlen,
            self.saltlen
        )
        return result.encode() # type: ignore
    #
    def verify(self, password: bytes, hash: bytes) -> bool:
        result = _internal.argontwoverify(password.decode(), hash.decode()) # type: ignore
        return result # type: ignore
    #
    @staticmethod
    def statichash(
        password: bytes,
        *,
        algorithm: Algorithm.Argon2 = Algorithm.Argon2.ID,
        version: int = 19,
        timecost: int = 3,
        memorycost: int = 65536,
        parallelism: int = 4,
        hashlen: int = 32,
        saltlen: int = 16
    ) -> bytes:
        match version:
            case 19:
                aversion = "0x13"
            case 16:
                aversion = "0x10"
            case _:
                raise ValueError("Err")
        #
        result = _internal.argontwohash(  # type: ignore
            Algorithm.Argon2(algorithm).value,
            aversion,
            password.decode(),
            timecost,
            memorycost,
            parallelism,
            hashlen,
            saltlen
        )
        return result.encode() # type: ignore
    #
    @staticmethod
    def staticverify(password: bytes, hash: bytes) -> bool:
        result = _internal.argontwoverify(password.decode(), hash.decode()) # type: ignore
        return result # type: ignore

class Bcrypt:
    def __init__(
            self,
            cost: int = 12
        ) -> None:
        self.cost = cost
        return None
    #
    def hash(self, password: bytes) -> bytes:
        result = _internal.bcrypthash(  # type: ignore
            password,
            self.cost
        )
        return result.encode() # type: ignore
    #
    def verify(self, password: bytes, hash: bytes) -> bool:
        result = _internal.bcryptverify(password, hash) # type: ignore
        return result # type: ignore
    #
    @staticmethod
    def statichash(
        password: bytes,
        *,
        cost: int = 12
    ) -> bytes:
        result = _internal.bcrypthash(  # type: ignore
            password,
            cost
        )
        return result.encode() # type: ignore
    #
    @staticmethod
    def staticverify(password: bytes, hash: bytes) -> bool:
        result = _internal.bcryptverify(password, hash) # type: ignore
        return result # type: ignore
