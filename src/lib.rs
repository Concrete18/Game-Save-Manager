use pyo3::prelude::*;
pub mod searcher;

/// Function that is run in Python.
#[pyfunction]
pub fn find_save_path(game_name: String, dirs_to_check: Vec<String>) -> PyResult<String> {
    let best_path = searcher::find_game_save_path(game_name, dirs_to_check);
    Ok(best_path.replace('\\', "/"))
}

/// A Python module implemented in Rust.
#[pymodule]
fn save_searcher(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(find_save_path, m)?)?;
    Ok(())
}
