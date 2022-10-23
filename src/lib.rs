use pyo3::prelude::*;
use walkdir::WalkDir;

/// Finds matches for `search_string` in `path`.
pub fn search_path(path: String, search_string: String) -> String {
    let mut found_path = "".to_string();
    for path in WalkDir::new(path)
        .max_depth(2)
        .into_iter()
        .filter_map(|e| e.ok())
    {
        let cur_path = String::from(path.path().to_string_lossy()).to_lowercase();
        // creates path variations
        let with_space = search_string.to_lowercase();
        let without_space = with_space.replace(' ', "");
        let with_underscore = with_space.replace(' ', "_");
        // sets return value
        if cur_path.contains(&with_space)
            || cur_path.contains(&without_space)
            || cur_path.contains(&with_underscore)
        {
            found_path = cur_path;
        }
    }
    found_path
}

/// Returns true if any value in `array` is in `string`.
pub fn any_val_in_string(string: String, array: [&str; 16]) -> bool {
    for item in array {
        if string.contains(item) {
            return true;
        }
    }
    false
}

/// Scores path points based on occurrences of
pub fn score_path(path: String) -> i32 {
    let score_pos = [
        "autosave",
        "quicksave",
        "manualsave",
        "saveslot",
        "sav.",
        ".sav",
        "config.ini",
        "userdata",
        "steam_autocloud",
        "Player.log",
        "slot",
        "screenshot",
        "save",
        ".zip",
        ".dat",
        "profile",
    ];
    let mut total_score = 0;
    for entry in WalkDir::new(path).into_iter().filter_map(|e| e.ok()) {
        let cur_path = String::from(entry.path().to_string_lossy()).to_lowercase();
        // TODO test switching to looping through score_pos here
        if any_val_in_string(cur_path, score_pos) {
            total_score += 25
        }
    }
    total_score
}

/// Finds the path that most likely leads to the games save folder by scoring each path.
pub fn pick_best_path(paths: Vec<String>) -> String {
    let mut best_score = 0;
    let mut best_path = &paths[0];
    for path in &paths {
        let score = score_path(path.to_string());
        if score > best_score {
            best_score = score;
            best_path = path;
        }
    }
    best_path.to_string()
}

/// TODO finish docstring
pub fn find_possible_save_paths(search_string: String, dirs_to_check: Vec<String>) -> Vec<String> {
    // let dirs_to_check = find_dirs_to_check();
    let mut possible_paths = Vec::new();
    for dir in dirs_to_check {
        let found_path = search_path(dir, search_string.to_string());
        if !found_path.is_empty() {
            possible_paths.push(found_path);
        }
    }
    possible_paths
}

/// Function that is run in Python.
#[pyfunction]
pub fn find_save_path(game_name: String, dirs_to_check: Vec<String>) -> PyResult<String> {
    // finds possible save paths
    let paths = find_possible_save_paths(game_name, dirs_to_check);
    let total_paths = paths.len();
    let best_path = match total_paths {
        0 => "".to_string(),
        1 => paths[0].clone(),
        _ => pick_best_path(paths),
    };
    Ok(best_path.replace('\\', "/"))
}

/// A Python module implemented in Rust.
#[pymodule]
fn save_search(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(find_save_path, m)?)?;
    Ok(())
}
