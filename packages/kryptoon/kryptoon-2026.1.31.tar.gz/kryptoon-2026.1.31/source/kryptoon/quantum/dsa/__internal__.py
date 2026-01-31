# IMPORT
from kryptoon import __internal__ as _internal # type: ignore
import typing as _typing
import enum as _enum

# MAIN
class Algorithm:
    class CROSS(_enum.Enum):
        CROSSR128B = "CrossRsdp128Balanced"
        CROSSR128F = "CrossRsdp128Fast"
        CROSSR128S = "CrossRsdp128Small"
        CROSSR192B = "CrossRsdp192Balanced"
        CROSSR192F = "CrossRsdp192Fast"
        CROSSR192S = "CrossRsdp192Small"
        CROSSR256B = "CrossRsdp256Balanced"
        CROSSR256F = "CrossRsdp256Fast"
        CROSSR256S = "CrossRsdp256Small"
        CROSSRG128B = "CrossRsdpg128Balanced"
        CROSSRG128F = "CrossRsdpg128Fast"
        CROSSRG128S = "CrossRsdpg128Small"
        CROSSRG192B = "CrossRsdpg192Balanced"
        CROSSRG192F = "CrossRsdpg192Fast"
        CROSSRG192S = "CrossRsdpg192Small"
        CROSSRG256B = "CrossRsdpg256Balanced"
        CROSSRG256F = "CrossRsdpg256Fast"
        CROSSRG256S = "CrossRsdpg256Small"
    #
    class DILITHIUM(_enum.Enum):
        DILITHIUM2 = "Dilithium2"
        DILITHIUM3 = "Dilithium3"
        DILITHIUM5 = "Dilithium5"
    #
    class FALCON(_enum.Enum):
        FALCON512 = "Falcon512"
        FALCON1024 = "Falcon1024"
    #
    class MAYO(_enum.Enum):
        MAYO1 = "Mayo1"
        MAYO2 = "Mayo2"
        MAYO3 = "Mayo3"
        MAYO5 = "Mayo5"
    #
    class MLDSA(_enum.Enum):
        MLDSA44 = "MlDsa44"
        MLDSA65 = "MlDsa65"
        MLDSA87 = "MlDsa87"
    #
    class SPHINCS(_enum.Enum):
        SHA2128F = "SphincsSha2128fSimple"
        SHA2128S = "SphincsSha2128sSimple"
        SHA2192F = "SphincsSha2192fSimple"
        SHA2192S = "SphincsSha2192sSimple"
        SHA2256F = "SphincsSha2256fSimple"
        SHA2256S = "SphincsSha2256sSimple"
        SHAKE128F = "SphincsShake128fSimple"
        SHAKE128S = "SphincsShake128sSimple"
        SHAKE192F = "SphincsShake192fSimple"
        SHAKE192S = "SphincsShake192sSimple"
        SHAKE256F = "SphincsShake256fSimple"
        SHAKE256S = "SphincsShake256sSimple"
    #
    class UOV(_enum.Enum):
        UOVOVIII = "UovOvIII"
        UOVOVIIIPKC = "UovOvIIIPkc"
        UOVOVIIIPKCSKC = "UovOvIIIPkcSkc"
        UOVOVIP = "UovOvIp"
        UOVOVIPPKC = "UovOvIpPkc"
        UOVOVIPPKCSKC = "UovOvIpPkcSkc"
        UOVOVIS = "UovOvIs"
        UOVOVISPKC = "UovOvIsPkc"
        UOVOVISPKCSKC = "UovOvIsPkcSkc"
        UOVOVV = "UovOvV"
        UOVOVVPKC = "UovOvVPkc"
        UOVOVVPKCSKC = "UovOvVPkcSkc"



class SecretKey:
    def __init__(self, secretkey: bytes) -> None:
        if not isinstance(secretkey, bytes):
            raise TypeError("SecretKey Not Valid")
        #
        self.secretkey = secretkey
        #
        return None
    #
    def sign(self, message: _typing.Any) -> _typing.Any:
        raise NotImplementedError()



class CROSSSecretKey(SecretKey):
    def __init__(self, name: Algorithm.CROSS, secretkey: bytes) -> None:
        if not isinstance(name, Algorithm.CROSS):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(secretkey)
        #
        self._algorithm = name
        #
        return None
    #
    def sign(self, message: bytes) -> bytes:
        signature: bytes = _internal.dsasign(self._algorithm.value, self.secretkey, message) # type: ignore
        return signature # type: ignore



class DILITHIUMSecretKey(SecretKey):
    def __init__(self, name: Algorithm.DILITHIUM, secretkey: bytes) -> None:
        if not isinstance(name, Algorithm.DILITHIUM):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(secretkey)
        #
        self._algorithm = name
        #
        return None
    #
    def sign(self, message: bytes) -> bytes:
        signature: bytes = _internal.dsasign(self._algorithm.value, self.secretkey, message) # type: ignore
        return signature # type: ignore



class FALCONSecretKey(SecretKey):
    def __init__(self, name: Algorithm.FALCON, secretkey: bytes) -> None:
        if not isinstance(name, Algorithm.FALCON):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(secretkey)
        #
        self._algorithm = name
        #
        return None
    #
    def sign(self, message: bytes) -> bytes:
        signature: bytes = _internal.dsasign(self._algorithm.value, self.secretkey, message) # type: ignore
        return signature # type: ignore



class MAYOSecretKey(SecretKey):
    def __init__(self, name: Algorithm.MAYO, secretkey: bytes) -> None:
        if not isinstance(name, Algorithm.MAYO):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(secretkey)
        #
        self._algorithm = name
        #
        return None
    #
    def sign(self, message: bytes) -> bytes:
        signature: bytes = _internal.dsasign(self._algorithm.value, self.secretkey, message) # type: ignore
        return signature # type: ignore



class MLDSASecretKey(SecretKey):
    def __init__(self, name: Algorithm.MLDSA, secretkey: bytes) -> None:
        if not isinstance(name, Algorithm.MLDSA):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(secretkey)
        #
        self._algorithm = name
        #
        return None
    #
    def sign(self, message: bytes) -> bytes:
        signature: bytes = _internal.dsasign(self._algorithm.value, self.secretkey, message) # type: ignore
        return signature # type: ignore



class SPHINCSSecretKey(SecretKey):
    def __init__(self, name: Algorithm.SPHINCS, secretkey: bytes) -> None:
        if not isinstance(name, Algorithm.SPHINCS):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(secretkey)
        #
        self._algorithm = name
        #
        return None
    #
    def sign(self, message: bytes) -> bytes:
        signature: bytes = _internal.dsasign(self._algorithm.value, self.secretkey, message) # type: ignore
        return signature # type: ignore



class UOVSecretKey(SecretKey):
    def __init__(self, name: Algorithm.UOV, secretkey: bytes) -> None:
        if not isinstance(name, Algorithm.UOV):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(secretkey)
        #
        self._algorithm = name
        #
        return None
    #
    def sign(self, message: bytes) -> bytes:
        signature: bytes = _internal.dsasign(self._algorithm.value, self.secretkey, message) # type: ignore
        return signature # type: ignore



class PublicKey:
    def __init__(self, publickey: bytes) -> None:
        if not isinstance(publickey, bytes):
            raise TypeError("PublicKey Not Valid")
        #
        self.publickey = publickey
        #
        return None
    #
    def verify(self, signature: _typing.Any, message: _typing.Any) -> _typing.Any:
        raise NotImplementedError()



class CROSSPublicKey(PublicKey):
    def __init__(self, name: Algorithm.CROSS, publickey: bytes) -> None:
        if not isinstance(name, Algorithm.CROSS):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(publickey)
        #
        self._algorithm = name
        #
        return None
    #
    def verify(self, signature: bytes, message: bytes) -> bool:
        result: bool = _internal.dsaverify(self._algorithm.value, self.publickey, signature, message) # type: ignore
        return result # type: ignore



class DILITHIUMPublicKey(PublicKey):
    def __init__(self, name: Algorithm.DILITHIUM, publickey: bytes) -> None:
        if not isinstance(name, Algorithm.DILITHIUM):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(publickey)
        #
        self._algorithm = name
        #
        return None
    #
    def verify(self, signature: bytes, message: bytes) -> bool:
        result: bool = _internal.dsaverify(self._algorithm.value, self.publickey, signature, message) # type: ignore
        return result # type: ignore



class FALCONPublicKey(PublicKey):
    def __init__(self, name: Algorithm.FALCON, publickey: bytes) -> None:
        if not isinstance(name, Algorithm.FALCON):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(publickey)
        #
        self._algorithm = name
        #
        return None
    #
    def verify(self, signature: bytes, message: bytes) -> bool:
        result: bool = _internal.dsaverify(self._algorithm.value, self.publickey, signature, message) # type: ignore
        return result # type: ignore



class MAYOPublicKey(PublicKey):
    def __init__(self, name: Algorithm.MAYO, publickey: bytes) -> None:
        if not isinstance(name, Algorithm.MAYO):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(publickey)
        #
        self._algorithm = name
        #
        return None
    #
    def verify(self, signature: bytes, message: bytes) -> bool:
        result: bool = _internal.dsaverify(self._algorithm.value, self.publickey, signature, message) # type: ignore
        return result # type: ignore



class MLDSAPublicKey(PublicKey):
    def __init__(self, name: Algorithm.MLDSA, publickey: bytes) -> None:
        if not isinstance(name, Algorithm.MLDSA):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(publickey)
        #
        self._algorithm = name
        #
        return None
    #
    def verify(self, signature: bytes, message: bytes) -> bool:
        result: bool = _internal.dsaverify(self._algorithm.value, self.publickey, signature, message) # type: ignore
        return result # type: ignore



class SPHINCSPublicKey(PublicKey):
    def __init__(self, name: Algorithm.SPHINCS, publickey: bytes) -> None:
        if not isinstance(name, Algorithm.SPHINCS):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(publickey)
        #
        self._algorithm = name
        #
        return None
    #
    def verify(self, signature: bytes, message: bytes) -> bool:
        result: bool = _internal.dsaverify(self._algorithm.value, self.publickey, signature, message) # type: ignore
        return result # type: ignore



class UOVPublicKey(PublicKey):
    def __init__(self, name: Algorithm.UOV, publickey: bytes) -> None:
        if not isinstance(name, Algorithm.UOV):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(publickey)
        #
        self._algorithm = name
        #
        return None
    #
    def verify(self, signature: bytes, message: bytes) -> bool:
        result: bool = _internal.dsaverify(self._algorithm.value, self.publickey, signature, message) # type: ignore
        return result # type: ignore



@_typing.overload
def KeyPair(
    name: Algorithm,
    *,
    secretkey: bytes, publickey: bytes
) -> tuple[SecretKey, PublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm, *, seed: bytes) -> SecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm, *, secretkey: bytes) -> SecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm, *, publickey: bytes) -> PublicKey: ...
@_typing.overload
def KeyPair(name: Algorithm) -> tuple[SecretKey, PublicKey]: ...



@_typing.overload
def KeyPair(
    name: Algorithm.CROSS,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[CROSSSecretKey, CROSSPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.CROSS, *, seed: bytes) -> CROSSSecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.CROSS, *, secretkey: bytes) -> CROSSSecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.CROSS, *, publickey: bytes) -> CROSSPublicKey: ...
@_typing.overload
def KeyPair(name: Algorithm.CROSS) -> tuple[CROSSSecretKey, CROSSPublicKey]: ...



@_typing.overload
def KeyPair(
    name: Algorithm.DILITHIUM,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[DILITHIUMSecretKey, DILITHIUMPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.DILITHIUM, *, seed: bytes) -> DILITHIUMSecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.DILITHIUM, *, secretkey: bytes) -> DILITHIUMSecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.DILITHIUM, *, publickey: bytes) -> DILITHIUMPublicKey: ...
@_typing.overload
def KeyPair(name: Algorithm.DILITHIUM) -> tuple[DILITHIUMSecretKey, DILITHIUMPublicKey]: ...



@_typing.overload
def KeyPair(
    name: Algorithm.FALCON,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[FALCONSecretKey, FALCONPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.FALCON, *, seed: bytes) -> FALCONSecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.FALCON, *, secretkey: bytes) -> FALCONSecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.FALCON, *, publickey: bytes) -> FALCONPublicKey: ...
@_typing.overload
def KeyPair(name: Algorithm.FALCON) -> tuple[FALCONSecretKey, FALCONPublicKey]: ...



@_typing.overload
def KeyPair(
    name: Algorithm.MAYO,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[MAYOSecretKey, MAYOPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.MAYO, *, seed: bytes) -> MAYOSecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.MAYO, *, secretkey: bytes) -> MAYOSecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.MAYO, *, publickey: bytes) -> MAYOPublicKey: ...
@_typing.overload
def KeyPair(name: Algorithm.MAYO) -> tuple[MAYOSecretKey, MAYOPublicKey]: ...



@_typing.overload
def KeyPair(
    name: Algorithm.MLDSA,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[MLDSASecretKey, MLDSAPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.MLDSA, *, seed: bytes) -> MLDSASecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.MLDSA, *, secretkey: bytes) -> MLDSASecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.MLDSA, *, publickey: bytes) -> MLDSAPublicKey: ...
@_typing.overload
def KeyPair(name: Algorithm.MLDSA) -> tuple[MLDSASecretKey, MLDSAPublicKey]: ...



@_typing.overload
def KeyPair(
    name: Algorithm.SPHINCS,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[SPHINCSSecretKey, SPHINCSPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.SPHINCS, *, seed: bytes) -> SPHINCSSecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.SPHINCS, *, secretkey: bytes) -> SPHINCSSecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.SPHINCS, *, publickey: bytes) -> SPHINCSPublicKey: ...
@_typing.overload
def KeyPair(name: Algorithm.SPHINCS) -> tuple[SPHINCSSecretKey, SPHINCSPublicKey]: ...



@_typing.overload
def KeyPair(
    name: Algorithm.UOV,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[UOVSecretKey, UOVPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.UOV, *, seed: bytes) -> UOVSecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.UOV, *, secretkey: bytes) -> UOVSecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.UOV, *, publickey: bytes) -> UOVPublicKey: ...
@_typing.overload
def KeyPair(name: Algorithm.UOV) -> tuple[UOVSecretKey, UOVPublicKey]: ...



Algorithms = Algorithm.CROSS | Algorithm.DILITHIUM | Algorithm.FALCON | Algorithm.MAYO | Algorithm.MLDSA | Algorithm.SPHINCS | Algorithm.UOV
def KeyPair(
        name: Algorithm | Algorithms,
        *,
        secretkey: bytes | None = None,
        publickey: bytes | None = None,
        seed: bytes | None = None
    ) -> tuple[SecretKey, PublicKey] | SecretKey | PublicKey:
    algorithm = name
    if isinstance(algorithm, Algorithm.CROSS):
        if seed is not None:
            secretkey, publickey = _internal.dsaseedkeygen(algorithm.value, seed)  # type: ignore
            return CROSSSecretKey(algorithm, secretkey), CROSSPublicKey(algorithm, publickey) # type: ignore
        elif secretkey is not None and publickey is None:
            return CROSSSecretKey(algorithm, secretkey)
        elif publickey is not None and secretkey is None:
            return CROSSPublicKey(algorithm, publickey)
        elif secretkey is not None and publickey is not None:
            return CROSSSecretKey(algorithm, secretkey), CROSSPublicKey(algorithm, publickey)
        else:
            secretkey, publickey = _internal.dsakeygen(algorithm.value) # type: ignore
            return CROSSSecretKey(algorithm, secretkey), CROSSPublicKey(algorithm, publickey) # type: ignore
    elif isinstance(algorithm, Algorithm.DILITHIUM):
        if seed is not None:
            secretkey, publickey = _internal.dsaseedkeygen(algorithm.value, seed)  # type: ignore
            return DILITHIUMSecretKey(algorithm, secretkey), DILITHIUMPublicKey(algorithm, publickey) # type: ignore
        elif secretkey is not None and publickey is None:
            return DILITHIUMSecretKey(algorithm, secretkey)
        elif publickey is not None and secretkey is None:
            return DILITHIUMPublicKey(algorithm, publickey)
        elif secretkey is not None and publickey is not None:
            return DILITHIUMSecretKey(algorithm, secretkey), DILITHIUMPublicKey(algorithm, publickey)
        else:
            secretkey, publickey = _internal.dsakeygen(algorithm.value) # type: ignore
            return DILITHIUMSecretKey(algorithm, secretkey), DILITHIUMPublicKey(algorithm, publickey) # type: ignore
    elif isinstance(algorithm, Algorithm.FALCON):
        if seed is not None:
            secretkey, publickey = _internal.dsaseedkeygen(algorithm.value, seed)  # type: ignore
            return FALCONSecretKey(algorithm, secretkey), FALCONPublicKey(algorithm, publickey) # type: ignore
        elif secretkey is not None and publickey is None:
            return FALCONSecretKey(algorithm, secretkey)
        elif publickey is not None and secretkey is None:
            return FALCONPublicKey(algorithm, publickey)
        elif secretkey is not None and publickey is not None:
            return FALCONSecretKey(algorithm, secretkey), FALCONPublicKey(algorithm, publickey)
        else:
            secretkey, publickey = _internal.dsakeygen(algorithm.value) # type: ignore
            return FALCONSecretKey(algorithm, secretkey), FALCONPublicKey(algorithm, publickey) # type: ignore
    elif isinstance(algorithm, Algorithm.MAYO):
        if seed is not None:
            secretkey, publickey = _internal.dsaseedkeygen(algorithm.value, seed)  # type: ignore
            return MAYOSecretKey(algorithm, secretkey), MAYOPublicKey(algorithm, publickey) # type: ignore
        elif secretkey is not None and publickey is None:
            return MAYOSecretKey(algorithm, secretkey)
        elif publickey is not None and secretkey is None:
            return MAYOPublicKey(algorithm, publickey)
        elif secretkey is not None and publickey is not None:
            return MAYOSecretKey(algorithm, secretkey), MAYOPublicKey(algorithm, publickey)
        else:
            secretkey, publickey = _internal.dsakeygen(algorithm.value) # type: ignore
            return MAYOSecretKey(algorithm, secretkey), MAYOPublicKey(algorithm, publickey) # type: ignore
    elif isinstance(algorithm, Algorithm.MLDSA):
        if seed is not None:
            secretkey, publickey = _internal.dsaseedkeygen(algorithm.value, seed)  # type: ignore
            return MLDSASecretKey(algorithm, secretkey), MLDSAPublicKey(algorithm, publickey) # type: ignore
        elif secretkey is not None and publickey is None:
            return MLDSASecretKey(algorithm, secretkey)
        elif publickey is not None and secretkey is None:
            return MLDSAPublicKey(algorithm, publickey)
        elif secretkey is not None and publickey is not None:
            return MLDSASecretKey(algorithm, secretkey), MLDSAPublicKey(algorithm, publickey)
        else:
            secretkey, publickey = _internal.dsakeygen(algorithm.value) # type: ignore
            return MLDSASecretKey(algorithm, secretkey), MLDSAPublicKey(algorithm, publickey) # type: ignore
    elif isinstance(algorithm, Algorithm.SPHINCS):
        if seed is not None:
            secretkey, publickey = _internal.dsaseedkeygen(algorithm.value, seed)  # type: ignore
            return SPHINCSSecretKey(algorithm, secretkey), SPHINCSPublicKey(algorithm, publickey) # type: ignore
        elif secretkey is not None and publickey is None:
            return SPHINCSSecretKey(algorithm, secretkey)
        elif publickey is not None and secretkey is None:
            return SPHINCSPublicKey(algorithm, publickey)
        elif secretkey is not None and publickey is not None:
            return SPHINCSSecretKey(algorithm, secretkey), SPHINCSPublicKey(algorithm, publickey)
        else:
            secretkey, publickey = _internal.dsakeygen(algorithm.value) # type: ignore
            return SPHINCSSecretKey(algorithm, secretkey), SPHINCSPublicKey(algorithm, publickey) # type: ignore
    elif isinstance(algorithm, Algorithm.UOV):
        if seed is not None:
            secretkey, publickey = _internal.dsaseedkeygen(algorithm.value, seed)  # type: ignore
            return UOVSecretKey(algorithm, secretkey), UOVPublicKey(algorithm, publickey) # type: ignore
        elif secretkey is not None and publickey is None:
            return UOVSecretKey(algorithm, secretkey)
        elif publickey is not None and secretkey is None:
            return UOVPublicKey(algorithm, publickey)
        elif secretkey is not None and publickey is not None:
            return UOVSecretKey(algorithm, secretkey), UOVPublicKey(algorithm, publickey)
        else:
            secretkey, publickey = _internal.dsakeygen(algorithm.value) # type: ignore
            return UOVSecretKey(algorithm, secretkey), UOVPublicKey(algorithm, publickey) # type: ignore
    else:
        raise ValueError(f"Unsupported algorithm: {name}")
