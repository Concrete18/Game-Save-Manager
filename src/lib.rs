use pyo3::prelude::*;
use walkdir::WalkDir;

/// Finds matches for `search_string` in `path`.
fn search_path(path: String, search_string: String) -> String {
    let mut found_path = "".to_string();
    for path in WalkDir::new(path)
        .max_depth(2)
        .into_iter()
        .filter_map(|e| e.ok())
    {
        let cur_path = String::from(path.path().to_string_lossy()).to_lowercase();
        // creates path variations
        let with_space = search_string.to_lowercase();
        let without_space = with_space.replace(" ", "");
        let with_underscore = with_space.replace(" ", "_");
        // sets return value
        if cur_path.contains(&with_space) {
            found_path = cur_path;
        } else if cur_path.contains(&without_space) {
            found_path = cur_path;
        } else if cur_path.contains(&with_underscore) {
            found_path = cur_path;
        }
    }
    found_path
}

/// Returns true if any value in `array` is in `string`.
fn any_val_in_string(string: String, array: [&str; 16]) -> bool {
    for item in array {
        if string.contains(item) {
            return true;
        }
    }
    false
}

/// Scores path points based on occurrences of
fn score_path(path: String) -> i32 {
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
            total_score = total_score + 25
        }
    }
    return total_score;
}

/// Finds the path that most likely leads to the games save folder by scoring each path.
fn pick_best_path(paths: Vec<String>) -> String {
    let mut best_score = 0;
    let mut best_path = &paths[0];
    for path in &paths {
        let score = score_path(path.to_string());
        if score > best_score {
            best_score = score;
            best_path = path;
        }
    }
    return best_path.to_string();
}

/// TODO finish docstring
fn find_possible_save_paths(search_string: String, dirs_to_check: Vec<String>) -> Vec<String> {
    // let dirs_to_check = find_dirs_to_check();
    let mut possible_paths = Vec::new();
    for dir in dirs_to_check {
        let found_path = search_path(dir, search_string.to_string());
        if found_path.len() > 0 {
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
    let mut best_path = "".to_string();
    if total_paths == 1 {
        best_path = paths[0].clone();
    } else if total_paths > 1 {
        best_path = pick_best_path(paths);
    }
    Ok(best_path.to_string().replace("\\", "/"))
}

/// A Python module implemented in Rust.
#[pymodule]
fn save_search(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(find_save_path, m)?)?;
    Ok(())
}

#[cfg(test)]
mod game_save_search_tests {
    use super::*;

    #[test]
    fn scoring_test() {
        let path = "c:/users/michael/appdata/local/teardown".to_string();
        let score = score_path(path);
        assert_eq!(score, 225);
    }

    fn find_dirs_to_check() -> Vec<String> {
        let dirs_to_check = vec![
            "D:/My Installed Games/Steam Games/steamapps/common".to_string(),
            "C:/Users/Michael/AppData/Local".to_string(),
            "C:/Users/Michael/AppData/LocalLow".to_string(),
            "C:/Users/Michael/AppData/Roaming".to_string(),
            "C:/Users/Michael/Saved Games".to_string(),
            "C:/Users/Michael/Documents".to_string(),
            "D:/My Documents".to_string(),
            "C:/Program Files (x86)/Steam/steamapps/common".to_string(),
        ];
        return dirs_to_check;
    }

    #[test]
    fn in_appdata() {
        let dirs_to_check = find_dirs_to_check();
        let found_path = find_save_path("Teardown".to_string(), dirs_to_check).unwrap();
        let actual_path = "c:/users/michael/appdata/local/teardown".to_string();
        println!("Found: {found_path}\nActual: {actual_path}");
        assert_eq!(found_path.contains(&actual_path), true);
    }

    #[test]
    fn in_steamapps() {
        let dirs_to_check = find_dirs_to_check();
        let found_path = find_save_path("Deep Rock Galactic".to_string(), dirs_to_check).unwrap();
        let actual_path =
            "d:/my installed games/steam games/steamapps/common/deep rock galactic".to_string();
        println!("Found: {found_path}\nActual: {actual_path}");
        assert_eq!(found_path.contains(&actual_path), true);
    }

    #[test]
    fn in_saved_games() {
        let dirs_to_check = find_dirs_to_check();
        let found_path = find_save_path("Cyberpunk 2077".to_string(), dirs_to_check).unwrap();
        let actual_path = "c:/users/michael/saved games/cd projekt red/cyberpunk 2077".to_string();
        println!("Found: {found_path}\nActual: {actual_path}");
        assert_eq!(found_path.contains(&actual_path), true);
    }

    #[test]
    fn no_space() {
        let dirs_to_check = find_dirs_to_check();
        let found_path = find_save_path("The Forest".to_string(), dirs_to_check).unwrap();
        let actual_path = "c:/users/michael/appdata/locallow/sks/theforest".to_string();
        println!("Found: {found_path}\nActual: {actual_path}");
        assert_eq!(found_path.contains(&actual_path), true);
    }

    #[test]
    fn has_underscore() {
        let dirs_to_check = find_dirs_to_check();
        let found_path = find_save_path("Vampire Survivor".to_string(), dirs_to_check).unwrap();
        let actual_path = "c:/users/michael/appdata/roaming/vampire_survivors_data".to_string();
        println!("Found: {found_path}\nActual: {actual_path}");
        assert_eq!(found_path.contains(&actual_path), true);
    }

    #[test]
    fn group_check() {
        let games = [
            (
                "Mini Motorways",
                "c:/users/michael/appdata/locallow/dinosaur polo club/mini motorways",
            ),
            (
                "Phantom Abyss",
                "c:/users/michael/appdata/local/phantomabyss/saved",
            ),
            (
                "Still There",
                "c:/users/michael/appdata/locallow/ghostshark games/still there",
            ),
            ("Wildfire", "c:/users/michael/appdata/local/wildfire"),
            (
                "Desperados III",
                "c:/users/michael/appdata/local/desperados iii",
            ),
            (
                "Manifold Garden",
                "c:/users/michael/appdata/locallow/william chyr studio/manifold garden",
            ),
            (
                "Boneworks",
                "c:/users/michael/appdata/locallow/stress level zero/boneworks",
            ),
            (
                "Dishonored 2",
                "c:/users/michael/saved games/arkane studios/dishonored2",
            ),
            ("Timberborn", "d:/my documents/timberborn/saves"),
        ];
        for (game, actual_path) in games {
            let dirs_to_check = find_dirs_to_check();
            let found_path = find_save_path(game.to_string(), dirs_to_check).unwrap();
            println!("\nFound: {found_path}\nActual: {actual_path}\n");
            assert_eq!(found_path.contains(&actual_path.to_string()), true);
        }
    }
}
