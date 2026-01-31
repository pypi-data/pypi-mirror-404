# IMPORT
import typing as _typing
import enum as _enum

# MAIN
class Algorithm:
    class BIKE(_enum.Enum):
        BIKEL1 = ...
        BIKEL3 = ...
        BIKEL5 = ...
    #
    class CLASSICMCELIECE(_enum.Enum):
        CLASSICMCELIECE348864 = ...
        CLASSICMCELIECE348864F = ...
        CLASSICMCELIECE460896 = ...
        CLASSICMCELIECE460896F = ...
        CLASSICMCELIECE6688128 = ...
        CLASSICMCELIECE6688128F = ...
        CLASSICMCELIECE6960119 = ...
        CLASSICMCELIECE6960119F = ...
        CLASSICMCELIECE8192128 = ...
        CLASSICMCELIECE8192128F = ...
    #
    class HQC(_enum.Enum):
        HQC128 = ...
        HQC192 = ...
        HQC256 = ...
    #
    class KYBER(_enum.Enum):
        KYBER512 = ...
        KYBER768 = ...
        KYBER1024 = ...
    #
    class MLKEM(_enum.Enum):
        MLKEM512 = ...
        MLKEM768 = ...
        MLKEM1024 = ...
    #
    class NTRUPRIME(_enum.Enum):
        NTRUPRIME = ...
    #
    class FRODOKEM(_enum.Enum):
        FRODOKEM640AES = ...
        FRODOKEM640SHAKE = ...
        FRODOKEM976AES = ...
        FRODOKEM976SHAKE = ...
        FRODOKEM1344AES = ...
        FRODOKEM1344SHAKE = ...



class SecretKey:
    def __init__(self, secretkey: bytes) -> None:
        self.secretkey = secretkey
        ...
    #
    def decapsulate(self, ciphertext: _typing.Any) -> _typing.Any:
        ...



class BIKESecretKey(SecretKey):
    def __init__(self, name: Algorithm.BIKE, secretkey: bytes) -> None:
        ...
    #
    def decapsulate(self, ciphertext: bytes) -> bytes:
        ...



class CLASSICMCELIECESecretKey(SecretKey):
    def __init__(self, name: Algorithm.CLASSICMCELIECE, secretkey: bytes) -> None:
        ...
    #
    def decapsulate(self, ciphertext: bytes) -> bytes:
        ...



class HQCSecretKey(SecretKey):
    def __init__(self, name: Algorithm.HQC, secretkey: bytes) -> None:
        ...
    #
    def decapsulate(self, ciphertext: bytes) -> bytes:
        ...



class KYBERSecretKey(SecretKey):
    def __init__(self, name: Algorithm.KYBER, secretkey: bytes) -> None:
        ...
    #
    def decapsulate(self, ciphertext: bytes) -> bytes:
        ...



class MLKEMSecretKey(SecretKey):
    def __init__(self, name: Algorithm.MLKEM, secretkey: bytes) -> None:
        ...
    #
    def decapsulate(self, ciphertext: bytes) -> bytes:
        ...



class NTRUPRIMESecretKey(SecretKey):
    def __init__(self, name: Algorithm.NTRUPRIME, secretkey: bytes) -> None:
        ...
    #
    def decapsulate(self, ciphertext: bytes) -> bytes:
        ...



class FRODOKEMSecretKey(SecretKey):
    def __init__(self, name: Algorithm.FRODOKEM, secretkey: bytes) -> None:
        ...
    #
    def decapsulate(self, ciphertext: bytes) -> bytes:
        ...



class PublicKey:
    def __init__(self, publickey: bytes) -> None:
        self.publickey = publickey
        ...
    #
    def encapsulate(self) -> tuple[_typing.Any, _typing.Any]:
        ...



class BIKEPublicKey(PublicKey):
    def __init__(self, name: Algorithm.BIKE, publickey: bytes) -> None:
        ...
    #
    def encapsulate(self) -> tuple[bytes, bytes]:
        ...



class CLASSICMCELIECEPublicKey(PublicKey):
    def __init__(self, name: Algorithm.CLASSICMCELIECE, publickey: bytes) -> None:
        ...
    #
    def encapsulate(self) -> tuple[bytes, bytes]:
        ...



class HQCPublicKey(PublicKey):
    def __init__(self, name: Algorithm.HQC, publickey: bytes) -> None:
        ...
    #
    def encapsulate(self) -> tuple[bytes, bytes]:
        ...



class KYBERPublicKey(PublicKey):
    def __init__(self, name: Algorithm.KYBER, publickey: bytes) -> None:
        ...
    #
    def encapsulate(self) -> tuple[bytes, bytes]:
        ...



class MLKEMPublicKey(PublicKey):
    def __init__(self, name: Algorithm.MLKEM, publickey: bytes) -> None:
        ...
    
    def encapsulate(self) -> tuple[bytes, bytes]:
        ...



class NTRUPRIMEPublicKey(PublicKey):
    def __init__(self, name: Algorithm.NTRUPRIME, publickey: bytes) -> None:
        ...
    #
    def encapsulate(self) -> tuple[bytes, bytes]:
        ...



class FRODOKEMPublicKey(PublicKey):
    def __init__(self, name: Algorithm.FRODOKEM, publickey: bytes) -> None:
        ...
    #
    def encapsulate(self) -> tuple[bytes, bytes]:
        ...



@_typing.overload
def KeyPair(
    name: Algorithm,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[SecretKey, PublicKey]:
    ...
@_typing.overload
def KeyPair(name: Algorithm, *, seed: bytes) -> tuple[SecretKey, PublicKey]:
    ...
@_typing.overload
def KeyPair(name: Algorithm, *, secretkey: bytes) -> SecretKey:
    ...
@_typing.overload
def KeyPair(name: Algorithm, *, publickey: bytes) -> PublicKey:
    ...
@_typing.overload
def KeyPair(name: Algorithm) -> tuple[SecretKey, PublicKey]:
    ...



@_typing.overload
def KeyPair(
    name: Algorithm.BIKE,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[BIKESecretKey, BIKEPublicKey]:
    ...
@_typing.overload
def KeyPair(name: Algorithm.BIKE, *, seed: bytes) -> tuple[BIKESecretKey, BIKEPublicKey]:
    ...
@_typing.overload
def KeyPair(name: Algorithm.BIKE, *, secretkey: bytes) -> BIKESecretKey:
    ...
@_typing.overload
def KeyPair(name: Algorithm.BIKE, *, publickey: bytes) -> BIKEPublicKey:
    ...
@_typing.overload
def KeyPair(name: Algorithm.BIKE) -> tuple[BIKESecretKey, BIKEPublicKey]:
    ...



@_typing.overload
def KeyPair(
    name: Algorithm.CLASSICMCELIECE,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[CLASSICMCELIECESecretKey, CLASSICMCELIECEPublicKey]:
    ...
@_typing.overload
def KeyPair(name: Algorithm.CLASSICMCELIECE, *, seed: bytes) -> tuple[CLASSICMCELIECESecretKey, CLASSICMCELIECEPublicKey]:
    ...
@_typing.overload
def KeyPair(name: Algorithm.CLASSICMCELIECE, *, secretkey: bytes) -> CLASSICMCELIECESecretKey:
    ...
@_typing.overload
def KeyPair(name: Algorithm.CLASSICMCELIECE, *, publickey: bytes) -> CLASSICMCELIECEPublicKey:
    ...
@_typing.overload
def KeyPair(name: Algorithm.CLASSICMCELIECE) -> tuple[CLASSICMCELIECESecretKey, CLASSICMCELIECEPublicKey]:
    ...



@_typing.overload
def KeyPair(
    name: Algorithm.HQC,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[HQCSecretKey, HQCPublicKey]:
    ...
@_typing.overload
def KeyPair(name: Algorithm.HQC, *, seed: bytes) -> tuple[HQCSecretKey, HQCPublicKey]:
    ...
@_typing.overload
def KeyPair(name: Algorithm.HQC, *, secretkey: bytes) -> HQCSecretKey:
    ...
@_typing.overload
def KeyPair(name: Algorithm.HQC, *, publickey: bytes) -> HQCPublicKey:
    ...
@_typing.overload
def KeyPair(name: Algorithm.HQC) -> tuple[HQCSecretKey, HQCPublicKey]:
    ...



@_typing.overload
def KeyPair(
    name: Algorithm.KYBER,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[KYBERSecretKey, KYBERPublicKey]:
    ...
@_typing.overload
def KeyPair(name: Algorithm.KYBER, *, seed: bytes) -> tuple[KYBERSecretKey, KYBERPublicKey]:
    ...
@_typing.overload
def KeyPair(name: Algorithm.KYBER, *, secretkey: bytes) -> KYBERSecretKey:
    ...
@_typing.overload
def KeyPair(name: Algorithm.KYBER, *, publickey: bytes) -> KYBERPublicKey:
    ...
@_typing.overload
def KeyPair(name: Algorithm.KYBER) -> tuple[KYBERSecretKey, KYBERPublicKey]:
    ...



@_typing.overload
def KeyPair(
    name: Algorithm.MLKEM,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[MLKEMSecretKey, MLKEMPublicKey]:
    ...
@_typing.overload
def KeyPair(name: Algorithm.MLKEM, *, seed: bytes) -> tuple[MLKEMSecretKey, MLKEMPublicKey]:
    ...
@_typing.overload
def KeyPair(name: Algorithm.MLKEM, *, secretkey: bytes) -> MLKEMSecretKey:
    ...
@_typing.overload
def KeyPair(name: Algorithm.MLKEM, *, publickey: bytes) -> MLKEMPublicKey:
    ...
@_typing.overload
def KeyPair(name: Algorithm.MLKEM) -> tuple[MLKEMSecretKey, MLKEMPublicKey]:
    ...



@_typing.overload
def KeyPair(
    name: Algorithm.NTRUPRIME,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[NTRUPRIMESecretKey, NTRUPRIMEPublicKey]:
    ...
@_typing.overload
def KeyPair(name: Algorithm.NTRUPRIME, *, seed: bytes) -> tuple[NTRUPRIMESecretKey, NTRUPRIMEPublicKey]:
    ...
@_typing.overload
def KeyPair(name: Algorithm.NTRUPRIME, *, secretkey: bytes) -> NTRUPRIMESecretKey:
    ...
@_typing.overload
def KeyPair(name: Algorithm.NTRUPRIME, *, publickey: bytes) -> NTRUPRIMEPublicKey:
    ...
@_typing.overload
def KeyPair(name: Algorithm.NTRUPRIME) -> tuple[NTRUPRIMESecretKey, NTRUPRIMEPublicKey]:
    ...



@_typing.overload
def KeyPair(
    name: Algorithm.FRODOKEM,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[FRODOKEMSecretKey, FRODOKEMPublicKey]:
    ...
@_typing.overload
def KeyPair(name: Algorithm.FRODOKEM, *, seed: bytes) -> tuple[FRODOKEMSecretKey, FRODOKEMPublicKey]:
    ...
@_typing.overload
def KeyPair(name: Algorithm.FRODOKEM, *, secretkey: bytes) -> FRODOKEMSecretKey:
    ...
@_typing.overload
def KeyPair(name: Algorithm.FRODOKEM, *, publickey: bytes) -> FRODOKEMPublicKey:
    ...
@_typing.overload
def KeyPair(name: Algorithm.FRODOKEM) -> tuple[FRODOKEMSecretKey, FRODOKEMPublicKey]:
    ...



Algorithms = Algorithm.BIKE | Algorithm.CLASSICMCELIECE | Algorithm.HQC | Algorithm.KYBER | Algorithm.MLKEM | Algorithm.NTRUPRIME | Algorithm.FRODOKEM
def KeyPair(
        name: Algorithm | Algorithms,
        *,
        secretkey: bytes | None = ...,
        publickey: bytes | None = ...,
        seed: bytes | None = ...
    ) -> tuple[SecretKey, PublicKey] | SecretKey | PublicKey:
    ...
