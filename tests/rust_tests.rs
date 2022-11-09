use save_searcher::*;

/// returns dirs for tests
fn find_dirs_to_check() -> Vec<String> {
    let dirs_to_check = vec![
        "C:/Program Files (x86)/Steam/steamapps/common".to_string(),
        "C:/Users/Michael/AppData/LocalLow".to_string(),
        "C:/Users/Michael/AppData/Roaming".to_string(),
        "C:/Users/Michael/AppData/Local".to_string(),
        "C:/Users/Michael/Saved Games".to_string(),
        "C:/Users/Michael/Documents".to_string(),
        "D:/My Installed Games/Steam Games/steamapps/common".to_string(),
        "D:/My Documents".to_string(),
    ];
    dirs_to_check
}

#[test]
fn find_possible_save_paths() {
    let string = "Cyberpunk 2077".to_string();
    let dirs_to_check = find_dirs_to_check();
    let paths = save_searcher::find_possible_save_paths(string, dirs_to_check);
    let answer = [
        "c:/users/michael/appdata/local\\cd projekt red\\cyberpunk 2077",
        "c:/users/michael/saved games\\cd projekt red\\cyberpunk 2077",
    ];
    assert_eq!(paths, answer);
}

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

#[test]
fn in_appdata() {
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // test vars
    let game_name = "Teardown";
    let actual_save = "c:/users/michael/appdata/local/teardown";
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert_eq!(found_path, actual_save.to_string());
}

#[test]
fn in_steamapps() {
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // test vars
    let game_name = "Deep Rock Galactic";
    let actual_save = "d:/my installed games/steam games/steamapps/common/deep rock galactic";
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert_eq!(found_path, actual_save.to_string());
}

#[test]
fn in_saved_games() {
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // test vars
    let game_name = "Cyberpunk 2077";
    let actual_save = "c:/users/michael/saved games/cd projekt red/cyberpunk 2077";
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert_eq!(found_path, actual_save.to_string());
}

#[test]
fn no_space() {
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // test vars
    let game_name = "The Forest";
    let actual_save = "c:/users/michael/appdata/locallow/sks/theforest";
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert_eq!(found_path, actual_save.to_string());
}

#[test]
fn has_underscore() {
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // test vars
    let game_name = "Vampire Survivor";
    let actual_save = "c:/users/michael/appdata/roaming/vampire_survivors_data";
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert_eq!(found_path, actual_save.to_string());
}

#[test]
fn contains_non_alphanumeric() {
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // test vars
    let game_name = "Batman™: Arkham Knight";
    let actual_save = "d:/my documents/wb games/batman arkham knight";
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert_eq!(found_path, actual_save.to_string());
}

#[test]
fn bonelab() {
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // test vars
    let game_name = "Bonelab";
    let actual_save = "c:/users/michael/appdata/localLow/stress Level zero/bonelav";
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert_eq!(found_path, actual_save.to_string());
}

#[test]
fn outer_wilds() {
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // test vars
    let game_name = "Outer Wilds";
    let actual_save = "c:/users/michael/appdata/locallow/mobius digital/outer wilds";
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert_eq!(found_path, actual_save.to_string());
}

#[test]
fn mini_motorway() {
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // test vars
    let game_name = "Mini Motorways";
    let actual_save = "c:/users/michael/appdata/locallow/dinosaur polo club/mini motorways";
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert_eq!(found_path, actual_save.to_string());
}

#[test]
fn phantom_abyss() {
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // test vars
    let game_name = "Phantom Abyss";
    let actual_save = "c:/users/michael/appdata/local/phantomabyss";
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert_eq!(found_path, actual_save.to_string());
}

#[test]
fn desperados_3() {
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // test vars
    let game_name = "Desperados III";
    let actual_save = "c:/users/michael/appdata/local/desperados iii";
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert_eq!(found_path, actual_save.to_string());
}

#[test]
fn manifold_garden() {
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // test vars
    let game_name = "Manifold Garden";
    let actual_save = "c:/users/michael/appdata/locallow/william chyr studio/manifold garden";
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert_eq!(found_path, actual_save.to_string());
}

#[test]
fn dishonored_2() {
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // test vars
    let game_name = "Dishonored 2";
    let actual_save = "c:/users/michael/saved games/arkane studios/dishonored2";
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert_eq!(found_path, actual_save.to_string());
}

#[test]
fn timberborn() {
    // get dirs
    let dirs_to_check = find_dirs_to_check();
    // test vars
    let game_name = "Timberborn";
    let actual_save = "d:/my documents/timberborn";
    // run test
    let found_path = find_save_path(game_name.to_string(), dirs_to_check).unwrap();
    assert_eq!(found_path, actual_save.to_string());
}

// TODO test bonelab with slot_0 added
// test the following after maturin dev has run again
// freshly frosted, rollerdrome, last call bbs and the rest below this entry
