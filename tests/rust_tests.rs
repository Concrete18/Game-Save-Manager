use save_searcher::*;

#[test]
fn scoring_test() {
    let path = "c:/users/michael/appdata/local/teardown".to_string();
    let score = save_searcher::score_path(path);
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
