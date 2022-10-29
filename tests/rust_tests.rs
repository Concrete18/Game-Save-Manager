use save_searcher::*;

#[test]
fn scoring_test() {
    let path = "c:/users/michael/appdata/local/teardown".to_string();
    let score = save_searcher::score_path(path);
    assert!(score >= 225);
}

#[test]
fn convert_to_alphanumeric() {
    let string = "Batman™: Arkham Knight".to_string();
    let new_string = save_searcher::to_alphanumeric(string);
    assert_eq!(new_string, "Batman Arkham Knight".to_string());
}

/// returns dirs for tests
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
    // test vars
    let game_name = "Teardown";
    let actual_save = "c:/users/michael/appdata/local/teardown";
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert!(found_path.contains(&actual_save.to_string()));
}

#[test]
fn in_steamapps() {
    // test vars
    let game_name = "Deep Rock Galactic";
    let actual_save = "d:/my installed games/steam games/steamapps/common/deep rock galactic";
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert!(found_path.contains(&actual_save.to_string()));
}

#[test]
fn in_saved_games() {
    // test vars
    let game_name = "Cyberpunk 2077";
    let actual_save = "c:/users/michael/saved games/cd projekt red/cyberpunk 2077";
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert!(found_path.contains(&actual_save.to_string()));
}

#[test]
fn no_space() {
    // test vars
    let game_name = "The Forest";
    let actual_save = "c:/users/michael/appdata/locallow/sks/theforest";
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert!(found_path.contains(&actual_save.to_string()));
}

#[test]
fn has_underscore() {
    // test vars
    let game_name = "Vampire Survivor";
    let actual_save = "c:/users/michael/appdata/roaming/vampire_survivors_data";
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert!(found_path.contains(&actual_save.to_string()));
}

#[test]
fn contains_non_alphanumeric() {
    // test vars
    let game_name = "Batman™: Arkham Knight";
    let actual_save = "d:/my documents/wb games/batman arkham knight";
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert!(found_path.contains(&actual_save.to_string()));
}

#[test]
fn mini_motorway() {
    // test vars
    let game_name = "Mini Motorways";
    let actual_save = "c:/users/michael/appdata/locallow/dinosaur polo club/mini motorways";
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert!(found_path.contains(&actual_save.to_string()));
}

#[test]
fn phantom_abyss() {
    // test vars
    let game_name = "Phantom Abyss";
    let actual_save = "c:/users/michael/appdata/local/phantomabyss/saved";
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert!(found_path.contains(&actual_save.to_string()));
}

#[test]
fn desperados_3() {
    // test vars
    let game_name = "Desperados III";
    let actual_save = "c:/users/michael/appdata/local/desperados iii";
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert!(found_path.contains(&actual_save.to_string()));
}

#[test]
fn manifold_garden() {
    // test vars
    let game_name = "Manifold Garden";
    let actual_save = "c:/users/michael/appdata/locallow/william chyr studio/manifold garden";
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert!(found_path.contains(&actual_save.to_string()));
}

#[test]
fn dishonored_2() {
    // test vars
    let game_name = "Dishonored 2";
    let actual_save = "c:/users/michael/saved games/arkane studios/dishonored2";
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert!(found_path.contains(&actual_save.to_string()));
}

#[test]
fn timberborn() {
    // test vars
    let game_name = "Timberborn";
    let actual_save = "d:/my documents/timberborn/saves";
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert!(found_path.contains(&actual_save.to_string()));
}
