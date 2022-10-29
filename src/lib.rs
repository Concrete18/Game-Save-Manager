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
    const SCORE_POS: [&str; 16] = [
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
        if any_val_in_string(cur_path, SCORE_POS) {
            total_score += 25;
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

// trait TakeRandom<T> {
//     fn take_random_item(self: &mut Self) -> T;
// }

// impl<T> TakeRandom<T> for Vec<T> {
//     fn take_random_item(self: &mut Self) -> T {
//         let mut rng = rand::thread_rng();
//         let i = rng.gen_range(0..self.len());
//         self.swap_remove(i)
//     }
// }

// trait ToAlphanumeric<T> {
//     fn to_alphanumeric(self: &mut Self) -> T;
// }

// impl<String> ToAlphanumeric<String> for String {
//     fn to_alphanumeric(self: &mut Self) -> String {
//         let mut cleaned_string = String::new();
//         for char in String.chars() {
//             if char.is_alphanumeric() || char == ' ' {
//                 cleaned_string.push(char)
//             }
//         }
//         if cleaned_string.is_empty() {
//             return "".to_string();
//         } else {
//             return cleaned_string;
//         }
//     }
// }

/// turns `string` into alphanumeric only.
/// TODO make into method on string
pub fn to_alphanumeric(string: String) -> String {
    let mut cleaned_string = "".to_string();
    for char in string.chars() {
        if char.is_alphanumeric() || char == ' ' {
            cleaned_string.push(char)
        }
    }
    cleaned_string
}

/// Function that is run in Python.
#[pyfunction]
pub fn find_save_path(game_name: String, dirs_to_check: Vec<String>) -> PyResult<String> {
    let cleaned_name = to_alphanumeric(game_name);
    // finds possible save paths
    let paths = find_possible_save_paths(cleaned_name, dirs_to_check);
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
fn save_searcher(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(find_save_path, m)?)?;
    Ok(())
}
