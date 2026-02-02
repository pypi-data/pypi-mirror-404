use pyo3::prelude::*;

mod parser;

mod telegram;
use telegram::format_for_telegram;

mod matrix;
use matrix::format_for_matrix;

mod general;
use general::format_body;

#[pymodule]
fn slidge_style_parser(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(format_body, m)?)?;
    m.add_function(wrap_pyfunction!(format_for_matrix, m)?)?;
    m.add_function(wrap_pyfunction!(format_for_telegram, m)?)?;
    Ok(())
}
