// IMPORT
use argon2::{password_hash::{PasswordHash, PasswordHasher, PasswordVerifier, SaltString, Error}, Argon2, Algorithm, Version, Params};
use rand::RngCore;
use bcrypt;
use pyo3::exceptions::*;
use pyo3::prelude::*;

// MAIN
fn argontwosalt(length: usize) -> Result<SaltString, PyErr> {
    if length < 8 {
        return Err(PyRuntimeError::new_err("Salt length must be at least 8 bytes"));
    } else {
        let mut salt = vec![0u8; length];
        rand::rng().fill_bytes(&mut salt);
        //
        SaltString::encode_b64(&salt)
            .map_err(|problem| PyRuntimeError::new_err(format!("Salt encoding error: {}", problem)))
    }
}

#[pyfunction]
pub fn argontwohash(
    algorithm: &str,
    version: Option<&str>,
    password: &str,
    timecost: u32,
    memorycost: u32,
    parallelism: u32,
    hashlen: usize,
    saltlen: Option<usize>
) -> PyResult<String> {
    let argontwo = match algorithm.to_lowercase().as_str() {
        "i" => Algorithm::Argon2i,
        "d" => Algorithm::Argon2d,
        "id" => Algorithm::Argon2id,
        other => {
            return Err(PyRuntimeError::new_err(format!("Unknown algorithm '{}'. Use 'i', 'd', or 'id'.", other)));
        }
    };
    let argontwoversion = match version {
        None => Version::default(),
        Some("0x10") => Version::V0x10,
        Some("0x13") => Version::V0x13,
        Some(version) => {
            return Err(PyRuntimeError::new_err(format!("Unknown version '{}'. Use '0x10', '0x13', or None.", version)))
        }
    };
    let salt = argontwosalt(saltlen.unwrap_or(16))?;
    //
    let params = Params::new(memorycost, timecost, parallelism, Some(hashlen))
        .map_err(|problem| PyRuntimeError::new_err(format!("Invalid parameters: {}", problem)))?;
    //
    let engine = Argon2::new(argontwo, argontwoversion, params);
    //
    let hash = engine
        .hash_password(password.as_bytes(), &salt)
        .map_err(|problem| PyRuntimeError::new_err(format!("Hashing error: {}", problem)))?;
    //
    Ok(hash.to_string())
}

#[pyfunction]
pub fn argontwoverify(password: &str, hash: &str) -> PyResult<bool> {
    let parsed = PasswordHash::new(hash)
        .map_err(|problem| PyRuntimeError::new_err(format!("Invalid hash: {}", problem)))?;
    //
    let engine = Argon2::default();
    //
    match engine.verify_password(password.as_bytes(), &parsed) {
        Ok(_) => Ok(true),
        Err(Error::Password) => Ok(false), // wrong password
        Err(problem) => Err(PyRuntimeError::new_err(format!("Verification error: {}", problem)))
    }
}

#[pyfunction]
pub fn bcrypthash(password: Vec<u8>, cost: u32) -> PyResult<String> {
    bcrypt::hash(password, cost)
        .map_err(|problem| PyRuntimeError::new_err(format!("Bcrypt error: {}", problem)))
}

#[pyfunction]
pub fn bcryptverify(password: Vec<u8>, hash: Vec<u8>) -> PyResult<bool> {
    let hashstring = std::str::from_utf8(&hash)
        .map_err(|problem| PyRuntimeError::new_err(format!("Invalid UTF-8 in hash: {}", problem)))?;
    //
    let result = bcrypt::verify(password, hashstring)
        .map_err(|problem| PyRuntimeError::new_err(format!("Bcrypt error: {}", problem)));
    Ok(result.is_ok())
}
