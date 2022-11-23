use aho_corasick::AhoCorasick;
use pyo3::prelude::*;
use walkdir::WalkDir;

/// Finds matches for `search_string` in `path`.
pub fn search_path(path: String, search_string: String) -> Vec<String> {
    let mut found_paths: Vec<String> = Vec::new();
    for path in WalkDir::new(path)
        .max_depth(2)
        .into_iter()
        .filter_map(|e| e.ok())
    {
        let cur_path = String::from(path.path().to_string_lossy()).to_lowercase();
        // creates path variations
        let with_space_string = &search_string.to_lowercase();
        let with_space = cur_path.contains(with_space_string);
        let without_space = cur_path.contains(&with_space_string.replace(' ', ""));
        let with_underscore = cur_path.contains(&with_space_string.replace(' ', "_"));
        // sets return value
        if with_space || without_space || with_underscore {
            // TODO make sure path is ignored if the base path already exists in found_paths
            found_paths.push(cur_path);
        }
    }
    // example of duplicate places to check
    // let test = [
    //         "c:/program files (x86)/steam/steamapps/common\\deep rock galactic",
    //         "c:/program files (x86)/steam/steamapps/common\\deep rock galactic\\engine",
    //         "c:/program files (x86)/steam/steamapps/common\\deep rock galactic\\fsd.exe",
    //     ];
    found_paths
}

/// Scores path points based on occurrences of
pub fn score_path(path: String) -> i32 {
    // positive scoring array
    const SCORE_POS: [&str; 20] = [
        "autosave",
        "quicksave",
        "manualsave",
        "saveslot",
        "SteamSaves",
        "Backup",
        "sav.",
        ".sav",
        "config.ini",
        "userdata",
        "steam_autocloud",
        "Player.log",
        "Player-prev.log",
        "output_log.txt",
        "slot",
        "screenshot",
        "save",
        ".zip",
        ".dat",
        "profile",
    ];
    let ac_pos = AhoCorasick::new(SCORE_POS);
    // negative scoring array
    const SCORE_NEG: [&str; 4] = ["nvidia", ".exe", ".dll", ".assets"];
    let ac_neg = AhoCorasick::new(SCORE_NEG);
    // get total score
    let mut total_score = 0;
    for entry in WalkDir::new(path).into_iter().filter_map(|e| e.ok()) {
        let cur_path = String::from(entry.path().to_string_lossy()).to_lowercase();

        for _match in ac_pos.find_iter(&cur_path) {
            total_score += 25;
        }

        for _match in ac_neg.find_iter(&cur_path) {
            total_score -= 30;
        }
    }
    total_score
}

/// Finds the path that most likely leads to the games save folder by scoring each path.
pub fn pick_best_path(paths: Vec<String>) -> String {
    let mut best_score = 0;
    let mut best_path = &paths[0];
    for path in &paths {
        if path.contains('.') {
            continue;
        }
        let score = score_path(path.to_string());
        if score > best_score {
            best_score = score;
            best_path = path;
        }
    }
    best_path.to_string()
}

/// Finds possible save paths for `search_string` within `dirs_to_check`.
pub fn find_possible_save_paths(search_string: String, dirs_to_check: Vec<String>) -> Vec<String> {
    let mut possible_paths = Vec::new();
    for dir in dirs_to_check {
        let found_paths = search_path(dir, search_string.to_string());
        if !found_paths.is_empty() {
            possible_paths.extend(found_paths);
        }
    }
    possible_paths
}

/// turns `string` into alphanumeric only.
pub fn to_alphanumeric(string: String) -> String {
    let mut cleaned_string = "".to_string();
    for char in string.chars() {
        if char.is_alphanumeric() || char == ' ' {
            cleaned_string.push(char)
        }
    }
    cleaned_string
}

// TODO move out of file

/// Function that is run in Python.
#[pyfunction]
pub fn find_save_path(game_name: String, dirs_to_check: Vec<String>) -> PyResult<String> {
    // TODO add errors
    let cleaned_name = to_alphanumeric(game_name);
    // finds possible save paths
    let paths = find_possible_save_paths(cleaned_name, dirs_to_check);
    // determines if multiples paths need to be scored so the best path can be picked
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
