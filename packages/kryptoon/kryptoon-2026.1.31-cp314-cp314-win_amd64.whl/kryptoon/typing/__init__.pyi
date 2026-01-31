# IMPORT
from kryptoon.quantum.dsa import __internal__ as __dsainternal
from kryptoon.quantum.kem import __internal__ as __keminternal

# MAIN
class PublicKey:
    InternalKEMPublicKey = __keminternal.PublicKey
    InternalDSAPublicKey = __dsainternal.PublicKey
    #
    BIKEPublicKey = __keminternal.BIKEPublicKey
    CLASSICMCELIECEPublicKey = __keminternal.CLASSICMCELIECEPublicKey
    HQCPublicKey = __keminternal.HQCPublicKey
    KYBERPublicKey = __keminternal.KYBERPublicKey
    MLKEMPublicKey = __keminternal.MLKEMPublicKey
    NTRUPRIMEPublicKey = __keminternal.NTRUPRIMEPublicKey
    FRODOKEMPublicKey = __keminternal.FRODOKEMPublicKey
    #
    CROSSPublicKey = __dsainternal.CROSSPublicKey
    DILITHIUMPublicKey = __dsainternal.DILITHIUMPublicKey
    FALCONPublicKey = __dsainternal.FALCONPublicKey
    MAYOPublicKey = __dsainternal.MAYOPublicKey
    MLDSAPublicKey = __dsainternal.MLDSAPublicKey
    SPHINCSPublicKey = __dsainternal.SPHINCSPublicKey
    UOVPublicKey = __dsainternal.UOVPublicKey

class SecretKey:
    InternalKEMSecretKey = __keminternal.SecretKey
    InternalDSASecretKey = __dsainternal.SecretKey
    #
    BIKESecretKey = __keminternal.BIKESecretKey
    CLASSICMCELIECESecretKey = __keminternal.CLASSICMCELIECESecretKey
    HQCSecretKey = __keminternal.HQCSecretKey
    KYBERSecretKey = __keminternal.KYBERSecretKey
    MLKEMSecretKey = __keminternal.MLKEMSecretKey
    NTRUPRIMESecretKey = __keminternal.NTRUPRIMESecretKey
    FRODOKEMSecretKey = __keminternal.FRODOKEMSecretKey
    #
    CROSSSecretKey = __dsainternal.CROSSSecretKey
    DILITHIUMSecretKey = __dsainternal.DILITHIUMSecretKey
    FALCONSecretKey = __dsainternal.FALCONSecretKey
    MAYOSecretKey = __dsainternal.MAYOSecretKey
    MLDSASecretKey = __dsainternal.MLDSASecretKey
    SPHINCSSecretKey = __dsainternal.SPHINCSSecretKey
    UOVSecretKey = __dsainternal.UOVSecretKey
