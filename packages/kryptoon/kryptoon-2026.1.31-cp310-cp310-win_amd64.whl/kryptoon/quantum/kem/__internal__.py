# IMPORT
from kryptoon import __internal__ as _internal # type: ignore
import typing as _typing
import enum as _enum

# MAIN
class Algorithm:
    class BIKE(_enum.Enum):
        BIKEL1 = "BikeL1"
        BIKEL3 = "BikeL3"
        BIKEL5 = "BikeL5"
    #
    class CLASSICMCELIECE(_enum.Enum):
        CLASSICMCELIECE348864 = "ClassicMcEliece348864"
        CLASSICMCELIECE348864F = "ClassicMcEliece348864f"
        CLASSICMCELIECE460896 = "ClassicMcEliece460896"
        CLASSICMCELIECE460896F = "ClassicMcEliece460896f"
        CLASSICMCELIECE6688128 = "ClassicMcEliece6688128"
        CLASSICMCELIECE6688128F = "ClassicMcEliece6688128f"
        CLASSICMCELIECE6960119 = "ClassicMcEliece6960119"
        CLASSICMCELIECE6960119F = "ClassicMcEliece6960119f"
        CLASSICMCELIECE8192128 = "ClassicMcEliece8192128"
        CLASSICMCELIECE8192128F = "ClassicMcEliece8192128f"
    #
    class HQC(_enum.Enum):
        HQC128 = "Hqc128"
        HQC192 = "Hqc192"
        HQC256 = "Hqc256"
    #
    class KYBER(_enum.Enum):
        KYBER512 = "Kyber512"
        KYBER768 = "Kyber768"
        KYBER1024 = "Kyber1024"
    #
    class MLKEM(_enum.Enum):
        MLKEM512 = "MlKem512"
        MLKEM768 = "MlKem768"
        MLKEM1024 = "MlKem1024"
    #
    class NTRUPRIME(_enum.Enum):
        NTRUPRIME = "NtruPrimeSntrup761"
    #
    class FRODOKEM(_enum.Enum):
        FRODOKEM640AES = "FrodoKem640Aes"
        FRODOKEM640SHAKE = "FrodoKem640Shake"
        FRODOKEM976AES = "FrodoKem976Aes"
        FRODOKEM976SHAKE = "FrodoKem976Shake"
        FRODOKEM1344AES = "FrodoKem1344Aes"
        FRODOKEM1344SHAKE = "FrodoKem1344Shake"



class SecretKey:
    def __init__(self, secretkey: bytes) -> None:
        if not isinstance(secretkey, bytes):
            raise TypeError("SecretKey Not Valid")
        #
        self.secretkey = secretkey
        #
        return None
    #
    def decapsulate(self, ciphertext: _typing.Any) -> _typing.Any:
        raise NotImplementedError()



class BIKESecretKey(SecretKey):
    def __init__(self, name: Algorithm.BIKE, secretkey: bytes) -> None:
        if not isinstance(name, Algorithm.BIKE):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(secretkey)
        #
        self._algorithm = name
        #
        return None
    #
    def decapsulate(self, ciphertext: bytes) -> bytes:
        sharedsecret: bytes = _internal.kemdecapsulate(self._algorithm.value, self.secretkey, ciphertext) # type: ignore
        return sharedsecret # type: ignore



class CLASSICMCELIECESecretKey(SecretKey):
    def __init__(self, name: Algorithm.CLASSICMCELIECE, secretkey: bytes) -> None:
        if not isinstance(name, Algorithm.CLASSICMCELIECE):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(secretkey)
        #
        self._algorithm = name
        #
        return None
    #
    def decapsulate(self, ciphertext: bytes) -> bytes:
        sharedsecret: bytes = _internal.kemdecapsulate(self._algorithm.value, self.secretkey, ciphertext) # type: ignore
        return sharedsecret # type: ignore



class HQCSecretKey(SecretKey):
    def __init__(self, name: Algorithm.HQC, secretkey: bytes) -> None:
        if not isinstance(name, Algorithm.HQC):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(secretkey)
        #
        self._algorithm = name
        #
        return None
    #
    def decapsulate(self, ciphertext: bytes) -> bytes:
        sharedsecret: bytes = _internal.kemdecapsulate(self._algorithm.value, self.secretkey, ciphertext) # type: ignore
        return sharedsecret # type: ignore



class KYBERSecretKey(SecretKey):
    def __init__(self, name: Algorithm.KYBER, secretkey: bytes) -> None:
        if not isinstance(name, Algorithm.KYBER):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(secretkey)
        #
        self._algorithm = name
        #
        return None
    #
    def decapsulate(self, ciphertext: bytes) -> bytes:
        sharedsecret: bytes = _internal.kemdecapsulate(self._algorithm.value, self.secretkey, ciphertext) # type: ignore
        return sharedsecret # type: ignore



class MLKEMSecretKey(SecretKey):
    def __init__(self, name: Algorithm.MLKEM, secretkey: bytes) -> None:
        if not isinstance(name, Algorithm.MLKEM):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(secretkey)
        #
        self._algorithm = name
        #
        return None
    #
    def decapsulate(self, ciphertext: bytes) -> bytes:
        sharedsecret: bytes = _internal.kemdecapsulate(self._algorithm.value, self.secretkey, ciphertext) # type: ignore
        return sharedsecret # type: ignore



class NTRUPRIMESecretKey(SecretKey):
    def __init__(self, name: Algorithm.NTRUPRIME, secretkey: bytes) -> None:
        if not isinstance(name, Algorithm.NTRUPRIME):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(secretkey)
        #
        self._algorithm = name
        #
        return None
    #
    def decapsulate(self, ciphertext: bytes) -> bytes:
        sharedsecret: bytes = _internal.kemdecapsulate(self._algorithm.value, self.secretkey, ciphertext) # type: ignore
        return sharedsecret # type: ignore



class FRODOKEMSecretKey(SecretKey):
    def __init__(self, name: Algorithm.FRODOKEM, secretkey: bytes) -> None:
        if not isinstance(name, Algorithm.FRODOKEM):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(secretkey)
        #
        self._algorithm = name
        #
        return None
    #
    def decapsulate(self, ciphertext: bytes) -> bytes:
        sharedsecret: bytes = _internal.kemdecapsulate(self._algorithm.value, self.secretkey, ciphertext) # type: ignore
        return sharedsecret # type: ignore



class PublicKey:
    def __init__(self, publickey: bytes) -> None:
        if not isinstance(publickey, bytes):
            raise TypeError("PublicKey Not Valid")
        #
        self.publickey = publickey
        #
        return None
    #
    def encapsulate(self) -> tuple[_typing.Any, _typing.Any]:
        raise NotImplementedError()



class BIKEPublicKey(PublicKey):
    def __init__(self, name: Algorithm.BIKE, publickey: bytes) -> None:
        if not isinstance(name, Algorithm.BIKE):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(publickey)
        #
        self._algorithm = name
        #
        return None
    #
    def encapsulate(self) -> tuple[bytes, bytes]:
        sharedsecret, ciphertext = _internal.kemencapsulate(self._algorithm.value, self.publickey) # type: ignore
        return sharedsecret, ciphertext # type: ignore



class CLASSICMCELIECEPublicKey(PublicKey):
    def __init__(self, name: Algorithm.CLASSICMCELIECE, publickey: bytes) -> None:
        if not isinstance(name, Algorithm.CLASSICMCELIECE):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(publickey)
        #
        self._algorithm = name
        #
        return None
    #
    def encapsulate(self) -> tuple[bytes, bytes]:
        sharedsecret, ciphertext = _internal.kemencapsulate(self._algorithm.value, self.publickey) # type: ignore
        return sharedsecret, ciphertext # type: ignore



class HQCPublicKey(PublicKey):
    def __init__(self, name: Algorithm.HQC, publickey: bytes) -> None:
        if not isinstance(name, Algorithm.HQC):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(publickey)
        #
        self._algorithm = name
        #
        return None
    #
    def encapsulate(self) -> tuple[bytes, bytes]:
        sharedsecret, ciphertext = _internal.kemencapsulate(self._algorithm.value, self.publickey) # type: ignore
        return sharedsecret, ciphertext # type: ignore



class KYBERPublicKey(PublicKey):
    def __init__(self, name: Algorithm.KYBER, publickey: bytes) -> None:
        if not isinstance(name, Algorithm.KYBER):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(publickey)
        #
        self._algorithm = name
        #
        return None
    #
    def encapsulate(self) -> tuple[bytes, bytes]:
        sharedsecret, ciphertext = _internal.kemencapsulate(self._algorithm.value, self.publickey) # type: ignore
        return sharedsecret, ciphertext # type: ignore



class MLKEMPublicKey(PublicKey):
    def __init__(self, name: Algorithm.MLKEM, publickey: bytes) -> None:
        if not isinstance(name, Algorithm.MLKEM):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(publickey)
        #
        self._algorithm = name
        #
        return None
    #
    def encapsulate(self) -> tuple[bytes, bytes]:
        sharedsecret, ciphertext = _internal.kemencapsulate(self._algorithm.value, self.publickey) # type: ignore
        return sharedsecret, ciphertext # type: ignore



class NTRUPRIMEPublicKey(PublicKey):
    def __init__(self, name: Algorithm.NTRUPRIME, publickey: bytes) -> None:
        if not isinstance(name, Algorithm.NTRUPRIME):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(publickey)
        #
        self._algorithm = name
        #
        return None
    #
    def encapsulate(self) -> tuple[bytes, bytes]:
        sharedsecret, ciphertext = _internal.kemencapsulate(self._algorithm.value, self.publickey) # type: ignore
        return sharedsecret, ciphertext # type: ignore



class FRODOKEMPublicKey(PublicKey):
    def __init__(self, name: Algorithm.FRODOKEM, publickey: bytes) -> None:
        if not isinstance(name, Algorithm.FRODOKEM):
            raise ValueError(f"Unsupported algorithm: {name}")
        else:
            super().__init__(publickey)
        #
        self._algorithm = name
        #
        return None
    #
    def encapsulate(self) -> tuple[bytes, bytes]:
        sharedsecret, ciphertext = _internal.kemencapsulate(self._algorithm.value, self.publickey) # type: ignore
        return sharedsecret, ciphertext # type: ignore



@_typing.overload
def KeyPair(
    name: Algorithm,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[SecretKey, PublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm, *, seed: bytes) -> tuple[SecretKey, PublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm, *, secretkey: bytes) -> SecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm, *, publickey: bytes) -> PublicKey: ...
@_typing.overload
def KeyPair(name: Algorithm) -> tuple[SecretKey, PublicKey]: ...



@_typing.overload
def KeyPair(
    name: Algorithm.BIKE,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[BIKESecretKey, BIKEPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.BIKE, *, seed: bytes) -> tuple[BIKESecretKey, BIKEPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.BIKE, *, secretkey: bytes) -> BIKESecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.BIKE, *, publickey: bytes) -> BIKEPublicKey: ...
@_typing.overload
def KeyPair(name: Algorithm.BIKE) -> tuple[BIKESecretKey, BIKEPublicKey]: ...



@_typing.overload
def KeyPair(
    name: Algorithm.CLASSICMCELIECE,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[CLASSICMCELIECESecretKey, CLASSICMCELIECEPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.CLASSICMCELIECE, *, seed: bytes) -> tuple[CLASSICMCELIECESecretKey, CLASSICMCELIECEPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.CLASSICMCELIECE, *, secretkey: bytes) -> CLASSICMCELIECESecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.CLASSICMCELIECE, *, publickey: bytes) -> CLASSICMCELIECEPublicKey: ...
@_typing.overload
def KeyPair(name: Algorithm.CLASSICMCELIECE) -> tuple[CLASSICMCELIECESecretKey, CLASSICMCELIECEPublicKey]: ...



@_typing.overload
def KeyPair(
    name: Algorithm.HQC,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[HQCSecretKey, HQCPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.HQC, *, seed: bytes) -> tuple[HQCSecretKey, HQCPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.HQC, *, secretkey: bytes) -> HQCSecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.HQC, *, publickey: bytes) -> HQCPublicKey: ...
@_typing.overload
def KeyPair(name: Algorithm.HQC) -> tuple[HQCSecretKey, HQCPublicKey]: ...



@_typing.overload
def KeyPair(
    name: Algorithm.KYBER,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[KYBERSecretKey, KYBERPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.KYBER, *, seed: bytes) -> tuple[KYBERSecretKey, KYBERPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.KYBER, *, secretkey: bytes) -> KYBERSecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.KYBER, *, publickey: bytes) -> KYBERPublicKey: ...
@_typing.overload
def KeyPair(name: Algorithm.KYBER) -> tuple[KYBERSecretKey, KYBERPublicKey]: ...



@_typing.overload
def KeyPair(
    name: Algorithm.MLKEM,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[MLKEMSecretKey, MLKEMPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.MLKEM, *, seed: bytes) -> tuple[MLKEMSecretKey, MLKEMPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.MLKEM, *, secretkey: bytes) -> MLKEMSecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.MLKEM, *, publickey: bytes) -> MLKEMPublicKey: ...
@_typing.overload
def KeyPair(name: Algorithm.MLKEM) -> tuple[MLKEMSecretKey, MLKEMPublicKey]: ...



@_typing.overload
def KeyPair(
    name: Algorithm.NTRUPRIME,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[NTRUPRIMESecretKey, NTRUPRIMEPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.NTRUPRIME, *, seed: bytes) -> tuple[NTRUPRIMESecretKey, NTRUPRIMEPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.NTRUPRIME, *, secretkey: bytes) -> NTRUPRIMESecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.NTRUPRIME, *, publickey: bytes) -> NTRUPRIMEPublicKey: ...
@_typing.overload
def KeyPair(name: Algorithm.NTRUPRIME) -> tuple[NTRUPRIMESecretKey, NTRUPRIMEPublicKey]: ...



@_typing.overload
def KeyPair(
    name: Algorithm.FRODOKEM,
    *,
    secretkey: bytes,
    publickey: bytes
) -> tuple[FRODOKEMSecretKey, FRODOKEMPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.FRODOKEM, *, seed: bytes) -> tuple[FRODOKEMSecretKey, FRODOKEMPublicKey]: ...
@_typing.overload
def KeyPair(name: Algorithm.FRODOKEM, *, secretkey: bytes) -> FRODOKEMSecretKey: ...
@_typing.overload
def KeyPair(name: Algorithm.FRODOKEM, *, publickey: bytes) -> FRODOKEMPublicKey: ...
@_typing.overload
def KeyPair(name: Algorithm.FRODOKEM) -> tuple[FRODOKEMSecretKey, FRODOKEMPublicKey]: ...



Algorithms = Algorithm.BIKE | Algorithm.CLASSICMCELIECE | Algorithm.HQC | Algorithm.KYBER | Algorithm.MLKEM | Algorithm.NTRUPRIME | Algorithm.FRODOKEM
def KeyPair(
        name: Algorithm | Algorithms,
        *,
        secretkey: bytes | None = None,
        publickey: bytes | None = None,
        seed: bytes | None = None
    ) -> tuple[SecretKey, PublicKey] | SecretKey | PublicKey:
    algorithm = name
    if isinstance(algorithm, Algorithm.BIKE):
        if seed is not None:
            secretkey, publickey = _internal.kemseedkeygen(algorithm.value, seed)  # type: ignore
            return BIKESecretKey(algorithm, secretkey), BIKEPublicKey(algorithm, publickey) # type: ignore
        elif secretkey is not None and publickey is None:
            return BIKESecretKey(algorithm, secretkey)
        elif publickey is not None and secretkey is None:
            return BIKEPublicKey(algorithm, publickey)
        elif secretkey is not None and publickey is not None:
            return BIKESecretKey(algorithm, secretkey), BIKEPublicKey(algorithm, publickey)
        else:
            secretkey, publickey = _internal.kemkeygen(algorithm.value) # type: ignore
            return BIKESecretKey(algorithm, secretkey), BIKEPublicKey(algorithm, publickey) # type: ignore
    elif isinstance(algorithm, Algorithm.CLASSICMCELIECE):
        if seed is not None:
            secretkey, publickey = _internal.kemseedkeygen(algorithm.value, seed)  # type: ignore
            return CLASSICMCELIECESecretKey(algorithm, secretkey), CLASSICMCELIECEPublicKey(algorithm, publickey) # type: ignore
        elif secretkey is not None and publickey is None:
            return CLASSICMCELIECESecretKey(algorithm, secretkey)
        elif publickey is not None and secretkey is None:
            return CLASSICMCELIECEPublicKey(algorithm, publickey)
        elif secretkey is not None and publickey is not None:
            return CLASSICMCELIECESecretKey(algorithm, secretkey), CLASSICMCELIECEPublicKey(algorithm, publickey)
        else:
            secretkey, publickey = _internal.kemkeygen(algorithm.value) # type: ignore
            return CLASSICMCELIECESecretKey(algorithm, secretkey), CLASSICMCELIECEPublicKey(algorithm, publickey) # type: ignore
    elif isinstance(algorithm, Algorithm.HQC):
        if seed is not None:
            secretkey, publickey = _internal.kemseedkeygen(algorithm.value, seed)  # type: ignore
            return HQCSecretKey(algorithm, secretkey), HQCPublicKey(algorithm, publickey) # type: ignore
        elif secretkey is not None and publickey is None:
            return HQCSecretKey(algorithm, secretkey)
        elif publickey is not None and secretkey is None:
            return HQCPublicKey(algorithm, publickey)
        elif secretkey is not None and publickey is not None:
            return HQCSecretKey(algorithm, secretkey), HQCPublicKey(algorithm, publickey)
        else:
            secretkey, publickey = _internal.kemkeygen(algorithm.value) # type: ignore
            return HQCSecretKey(algorithm, secretkey), HQCPublicKey(algorithm, publickey) # type: ignore
    elif isinstance(algorithm, Algorithm.KYBER):
        if seed is not None:
            secretkey, publickey = _internal.kemseedkeygen(algorithm.value, seed)  # type: ignore
            return KYBERSecretKey(algorithm, secretkey), KYBERPublicKey(algorithm, publickey) # type: ignore
        elif secretkey is not None and publickey is None:
            return KYBERSecretKey(algorithm, secretkey)
        elif publickey is not None and secretkey is None:
            return KYBERPublicKey(algorithm, publickey)
        elif secretkey is not None and publickey is not None:
            return KYBERSecretKey(algorithm, secretkey), KYBERPublicKey(algorithm, publickey)
        else:
            secretkey, publickey = _internal.kemkeygen(algorithm.value) # type: ignore
            return KYBERSecretKey(algorithm, secretkey), KYBERPublicKey(algorithm, publickey) # type: ignore
    elif isinstance(algorithm, Algorithm.MLKEM):
        if seed is not None:
            secretkey, publickey = _internal.kemseedkeygen(algorithm.value, seed)  # type: ignore
            return MLKEMSecretKey(algorithm, secretkey), MLKEMPublicKey(algorithm, publickey) # type: ignore
        elif secretkey is not None and publickey is None:
            return MLKEMSecretKey(algorithm, secretkey)
        elif publickey is not None and secretkey is None:
            return MLKEMPublicKey(algorithm, publickey)
        elif secretkey is not None and publickey is not None:
            return MLKEMSecretKey(algorithm, secretkey), MLKEMPublicKey(algorithm, publickey)
        else:
            secretkey, publickey = _internal.kemkeygen(algorithm.value) # type: ignore
            return MLKEMSecretKey(algorithm, secretkey), MLKEMPublicKey(algorithm, publickey) # type: ignore
    elif isinstance(algorithm, Algorithm.NTRUPRIME):
        if seed is not None:
            secretkey, publickey = _internal.kemseedkeygen(algorithm.value, seed)  # type: ignore
            return NTRUPRIMESecretKey(algorithm, secretkey), NTRUPRIMEPublicKey(algorithm, publickey) # type: ignore
        elif secretkey is not None and publickey is None:
            return NTRUPRIMESecretKey(algorithm, secretkey)
        elif publickey is not None and secretkey is None:
            return NTRUPRIMEPublicKey(algorithm, publickey)
        elif secretkey is not None and publickey is not None:
            return NTRUPRIMESecretKey(algorithm, secretkey), NTRUPRIMEPublicKey(algorithm, publickey)
        else:
            secretkey, publickey = _internal.kemkeygen(algorithm.value) # type: ignore
            return NTRUPRIMESecretKey(algorithm, secretkey), NTRUPRIMEPublicKey(algorithm, publickey) # type: ignore
    elif isinstance(algorithm, Algorithm.FRODOKEM):
        if seed is not None:
            secretkey, publickey = _internal.kemseedkeygen(algorithm.value, seed)  # type: ignore
            return FRODOKEMSecretKey(algorithm, secretkey), FRODOKEMPublicKey(algorithm, publickey) # type: ignore
        elif secretkey is not None and publickey is None:
            return FRODOKEMSecretKey(algorithm, secretkey)
        elif publickey is not None and secretkey is None:
            return FRODOKEMPublicKey(algorithm, publickey)
        elif secretkey is not None and publickey is not None:
            return FRODOKEMSecretKey(algorithm, secretkey), FRODOKEMPublicKey(algorithm, publickey)
        else:
            secretkey, publickey = _internal.kemkeygen(algorithm.value) # type: ignore
            return FRODOKEMSecretKey(algorithm, secretkey), FRODOKEMPublicKey(algorithm, publickey) # type: ignore
    else:
        raise ValueError(f"Unsupported algorithm: {name}")
