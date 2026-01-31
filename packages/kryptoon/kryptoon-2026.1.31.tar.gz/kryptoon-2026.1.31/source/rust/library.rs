// IMPORT
use pyo3::prelude::*;
mod backend;

// MAIN
#[pymodule]
fn __internal__(module: &Bound<PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(backend::classic::encode::internal::b58encode, module)?)?;
    module.add_function(wrap_pyfunction!(backend::classic::encode::internal::b58decode, module)?)?;
    //
    module.add_function(wrap_pyfunction!(backend::classic::phf::internal::argontwohash, module)?)?;
    module.add_function(wrap_pyfunction!(backend::classic::phf::internal::argontwoverify, module)?)?;
    module.add_function(wrap_pyfunction!(backend::classic::phf::internal::bcrypthash, module)?)?;
    module.add_function(wrap_pyfunction!(backend::classic::phf::internal::bcryptverify, module)?)?;
    //
    module.add_function(wrap_pyfunction!(backend::quantum::dsa::internal::dsakeygen, module)?)?;
    module.add_function(wrap_pyfunction!(backend::quantum::dsa::internal::dsaseedkeygen, module)?)?;
    module.add_function(wrap_pyfunction!(backend::quantum::dsa::internal::dsasign, module)?)?;
    module.add_function(wrap_pyfunction!(backend::quantum::dsa::internal::dsaverify, module)?)?;
    //
    module.add_function(wrap_pyfunction!(backend::quantum::kem::internal::kemkeygen, module)?)?;
    module.add_function(wrap_pyfunction!(backend::quantum::kem::internal::kemseedkeygen, module)?)?;
    module.add_function(wrap_pyfunction!(backend::quantum::kem::internal::kemencapsulate, module)?)?;
    module.add_function(wrap_pyfunction!(backend::quantum::kem::internal::kemdecapsulate, module)?)?;
    //
    module.add_class::<backend::classic::hash::internal::BLAKE3>()?;
    module.add_class::<backend::classic::hash::internal::RIPEMD128>()?;
    module.add_class::<backend::classic::hash::internal::RIPEMD160>()?;
    module.add_class::<backend::classic::hash::internal::RIPEMD256>()?;
    module.add_class::<backend::classic::hash::internal::RIPEMD320>()?;
    module.add_class::<backend::classic::hash::internal::KECCAK224>()?;
    module.add_class::<backend::classic::hash::internal::KECCAK256>()?;
    module.add_class::<backend::classic::hash::internal::KECCAK384>()?;
    module.add_class::<backend::classic::hash::internal::KECCAK512>()?;
    //
    Ok(())
}
