// IMPORT
use oqs::kem::{Algorithm, Kem};
use pyo3::exceptions::*;
use pyo3::prelude::*;

// MAIN
fn kemalgorithm(name: &str) -> Result<Kem, PyErr> {
    let algorithm = match name {
        "BikeL1" => Algorithm::BikeL1,
        "BikeL3" => Algorithm::BikeL3,
        "BikeL5" => Algorithm::BikeL5,
        //
        "ClassicMcEliece348864" => Algorithm::ClassicMcEliece348864,
        "ClassicMcEliece348864f" => Algorithm::ClassicMcEliece348864f,
        "ClassicMcEliece460896" => Algorithm::ClassicMcEliece460896,
        "ClassicMcEliece460896f" => Algorithm::ClassicMcEliece460896f,
        "ClassicMcEliece6688128" => Algorithm::ClassicMcEliece6688128,
        "ClassicMcEliece6688128f" => Algorithm::ClassicMcEliece6688128f,
        "ClassicMcEliece6960119" => Algorithm::ClassicMcEliece6960119,
        "ClassicMcEliece6960119f" => Algorithm::ClassicMcEliece6960119f,
        "ClassicMcEliece8192128" => Algorithm::ClassicMcEliece8192128,
        "ClassicMcEliece8192128f" => Algorithm::ClassicMcEliece8192128f,
        //
        "Hqc128" => Algorithm::Hqc128,
        "Hqc192" => Algorithm::Hqc192,
        "Hqc256" => Algorithm::Hqc256,
        //
        "Kyber512" => Algorithm::Kyber512,
        "Kyber768" => Algorithm::Kyber768,
        "Kyber1024" => Algorithm::Kyber1024,
        //
        "MlKem768" => Algorithm::MlKem768,
        "MlKem512" => Algorithm::MlKem512,
        "MlKem1024" => Algorithm::MlKem1024,
        //
        "NtruPrimeSntrup761" => Algorithm::NtruPrimeSntrup761,
        //
        "FrodoKem1344Aes" => Algorithm::FrodoKem1344Aes,
        "FrodoKem1344Shake" => Algorithm::FrodoKem1344Shake,
        "FrodoKem640Aes" => Algorithm::FrodoKem640Aes,
        "FrodoKem640Shake" => Algorithm::FrodoKem640Shake,
        "FrodoKem976Aes" => Algorithm::FrodoKem976Aes,
        "FrodoKem976Shake" => Algorithm::FrodoKem976Shake,
        _ => return Err(PyRuntimeError::new_err(format!("Unsupported algorithm: {}", name))),
    };
    let result = Kem::new(algorithm)
        .map_err(|problem| PyRuntimeError::new_err(format!("Algorithm failure: {}", problem)))?;
    //
    Ok(result)
}

#[pyfunction]
pub fn kemkeygen(name: &str) -> PyResult<(Vec<u8>, Vec<u8>)> {
    let algorithm = kemalgorithm(name)?;
    let (publickey, secretkey) = algorithm
        .keypair()
        .map_err(|problem| PyRuntimeError::new_err(format!("Algorithm failure: {}", problem)))?;
    //
    Ok((secretkey.into_vec(), publickey.into_vec()))
}

#[pyfunction]
pub fn kemseedkeygen(name: &str, seed: &[u8]) -> PyResult<(Vec<u8>, Vec<u8>)> {
    let algorithm = kemalgorithm(name)?;
    //
    let expected_len = algorithm.length_keypair_seed();
    if seed.len() != expected_len {
        return Err(PyRuntimeError::new_err(
            format!("Seed must be exactly {} bytes for {}, got {} bytes", 
                    expected_len, name, seed.len())
        ));
    }
    //
    let inseed = algorithm
        .keypair_seed_from_bytes(seed)
        .ok_or_else(|| PyRuntimeError::new_err("Invalid seed for keypair generation"))?;
    //
    let (publickey, secretkey) = algorithm
        .keypair_derand(&inseed)
        .map_err(|problem| PyRuntimeError::new_err(format!("Algorithm failure: {}", problem)))?;
    //
    Ok((secretkey.into_vec(), publickey.into_vec()))
}

#[pyfunction]
pub fn kemencapsulate(name: &str, publickey: &[u8]) -> PyResult<(Vec<u8>, Vec<u8>)> {
    let algorithm = kemalgorithm(name)?;
    let publickey = algorithm
        .public_key_from_bytes(publickey)
        .ok_or_else(|| PyRuntimeError::new_err("Invalid PublicKey"))?;
    let (ciphertext, sharedsecret) = algorithm
        .encapsulate(publickey)
        .map_err(|problem| PyRuntimeError::new_err(format!("Algorithm failure: {}", problem)))?;
    //
    Ok((sharedsecret.into_vec(), ciphertext.into_vec()))
}

#[pyfunction]
pub fn kemdecapsulate(name: &str, secretkey: &[u8], ciphertext: &[u8]) -> PyResult<Vec<u8>> {
    let algorithm = kemalgorithm(name)?;
    let secretkey = algorithm
        .secret_key_from_bytes(secretkey)
        .ok_or_else(|| PyRuntimeError::new_err("Invalid SecretKey"))?;
    let ciphertext = algorithm
        .ciphertext_from_bytes(ciphertext)
        .ok_or_else(|| PyRuntimeError::new_err("Invalid Ciphertext"))?;
    let sharedsecret = algorithm
        .decapsulate(secretkey, ciphertext)
        .map_err(|problem| PyRuntimeError::new_err(format!("Algorithm failure: {}", problem)))?;
    //
    Ok(sharedsecret.into_vec())
}
