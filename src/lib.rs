use pyo3::prelude::*;
use std::env;
use walkdir::WalkDir;

fn remove_whitespace(s: &str) -> String {
    s.split_whitespace().collect()
}

fn search_path(path: String, search_string: String) -> String {
    let mut found_path = "".to_string();
    for entry in WalkDir::new(path)
        .max_depth(2)
        .into_iter()
        .filter_map(|e| e.ok())
    {
        let cur_path = String::from(entry.path().to_string_lossy()).to_lowercase();
        let with_space = search_string.to_lowercase();
        let without_space = remove_whitespace(&search_string.to_lowercase());
        if cur_path.contains(&with_space) {
            found_path = cur_path;
        } else if cur_path.contains(&without_space) {
            found_path = cur_path;
        }
    }
    found_path
}

fn find_possible_save_paths(search_string: &String, dirs_to_check: Vec<String>) -> Vec<String> {
    // let dirs_to_check = find_dirs_to_check();
    let mut possible_paths = Vec::new();
    for dir in dirs_to_check {
        let found_path = search_path(dir.to_string(), search_string.to_string());
        if found_path.len() > 0 {
            possible_paths.push(found_path);
        }
    }
    possible_paths
}

fn any_val_in_string(string: String, array: [&str; 16]) -> bool {
    for item in array {
        if string.contains(item) {
            return true;
        }
    }
    false
}

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
        if any_val_in_string(cur_path, score_pos) {
            total_score = total_score + 25
        }
    }
    return total_score;
}

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

// fn main() {
//     let args: Vec<String> = env::args().collect();
//     let game = args[1].to_string();
//     let mut dirs_to_check: Vec<String> = Vec::new();
//     for i in 2..args.len() {
//         let dir = args[i].to_string();
//         dirs_to_check.push(dir);
//     }
//     if dirs_to_check.len() < 1 {
//         println!("No paths found to search.")
//     }

//     let best_path = find_save_path(game, dirs_to_check);
//     println!("{best_path}");
// }

/// Formats the sum of two numbers as string.
#[pyfunction]
fn find_save_path(game_name: String, dirs_to_check: Vec<String>) -> PyResult<String> {
    let paths = find_possible_save_paths(&game_name, dirs_to_check);
    let total_paths = paths.len();
    let mut best_path = String::new();
    if total_paths == 0 {
        best_path = "".to_string();
    } else if paths.len() == 1 {
        best_path = paths[0].clone();
    } else {
        best_path = pick_best_path(paths);
    }
    Ok(best_path.to_string())
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
    fn teardown() {
        let dirs_to_check = find_dirs_to_check();
        let found_path = find_save_path("Teardown".to_string(), dirs_to_check);
        let actual_path = "c:/users/michael/appdata/local\\teardown".to_string();
        println!("Found: {found_path}\nActual: {actual_path}");
        assert_eq!(found_path.contains(&actual_path), true);
    }

    #[test]
    fn deep_rock_galactic() {
        let dirs_to_check = find_dirs_to_check();
        let found_path = find_save_path("Deep Rock Galactic".to_string(), dirs_to_check);
        let actual_path =
            "d:/my installed games/steam games/steamapps/common\\deep rock galactic".to_string();
        println!("Found: {found_path}\nActual: {actual_path}");
        assert_eq!(found_path.contains(&actual_path), true);
    }

    #[test]
    fn the_forest() {
        let dirs_to_check = find_dirs_to_check();
        let found_path = find_save_path("The Forest".to_string(), dirs_to_check);
        let actual_path = "c:/users/michael/appdata/locallow\\sks\\theforest".to_string();
        println!("Found: {found_path}\nActual: {actual_path}");
        assert_eq!(found_path.contains(&actual_path), true);
    }

    #[test]
    fn factorio() {
        let dirs_to_check = find_dirs_to_check();
        let found_path = find_save_path("Factorio".to_string(), dirs_to_check);
        let actual_path = "c:/users/michael/appdata/roaming\\factorio\\".to_string();
        println!("Found: {found_path}\nActual: {actual_path}");
        assert_eq!(found_path.contains(&actual_path), true);
    }

    #[test]
    fn cyberpunk_2077() {
        let dirs_to_check = find_dirs_to_check();
        let found_path = find_save_path("Cyberpunk 2077".to_string(), dirs_to_check);
        let actual_path =
            "c:/users/michael/saved games\\cd projekt red\\cyberpunk 2077".to_string();
        println!("Found: {found_path}\nActual: {actual_path}");
        assert_eq!(found_path.contains(&actual_path), true);
    }

    #[test]
    fn check_rest() {
        let games = [
            (
                "Mini Motorways",
                "c:/users/michael/appdata/locallow\\dinosaur polo club\\mini motorways",
            ),
            (
                "Phantom Abyss",
                "c:/users/michael/appdata/local\\phantomabyss\\saved",
            ),
            (
                "Still There",
                "c:/users/michael/appdata/locallow\\ghostshark games\\still there",
            ),
            ("Wildfire", "c:/users/michael/appdata/local\\wildfire"),
            (
                "Desperados III",
                "c:/users/michael/appdata/local\\desperados iii",
            ),
            (
                "Manifold Garden",
                "c:/users/michael/appdata/locallow\\william chyr studio\\manifold garden",
            ),
            (
                "Boneworks",
                "c:/users/michael/appdata/locallow\\stress level zero\\boneworks",
            ),
            (
                "Dishonored 2",
                "c:/users/michael/saved games\\arkane studios\\dishonored2",
            ),
            ("Timberborn", "d:/my documents\\timberborn\\saves"),
            // TODO fix below entry
            // (
            //     "XCOM 2 War of the Chosen",
            //     "D:\\My Documents\\My Games\\XCOM2 War of the Chosen",
            // ),
        ];
        for (game, actual_path) in games {
            let dirs_to_check = find_dirs_to_check();
            let found_path = find_save_path(game.to_string(), dirs_to_check);
            println!("\nFound: {found_path}\nActual: {actual_path}\n");
            assert_eq!(found_path.contains(&actual_path.to_string()), true);
        }
    }
}
