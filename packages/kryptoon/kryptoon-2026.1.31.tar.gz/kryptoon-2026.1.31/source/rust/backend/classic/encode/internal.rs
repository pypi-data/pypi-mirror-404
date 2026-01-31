// IMPORT
use bs58::{encode, decode};
use pyo3::exceptions::*;
use pyo3::prelude::*;

// MAIN
#[pyfunction]
pub fn b58encode(buffer: Vec<u8>) -> PyResult<Vec<u8>> {
    let result = encode(buffer).into_vec();
    Ok(result)
}

#[pyfunction]
pub fn b58decode(buffer: Vec<u8>) -> PyResult<Vec<u8>> {
    let result = decode(buffer).into_vec()
        .map_err(|problem| PyRuntimeError::new_err(format!("Algorithm failure: {}", problem)))?;
    Ok(result)
}
