use criterion::{black_box, criterion_group, criterion_main, Criterion};
use save_searcher::searcher;

fn criterion_benchmark(c: &mut Criterion) {
    let dirs_to_check: Vec<String> = black_box(vec![
        "D:/My Installed Games/Steam Games/steamapps/common".to_string(),
        "C:/Users/Michael/AppData/Local".to_string(),
        "C:/Users/Michael/AppData/LocalLow".to_string(),
        "C:/Users/Michael/AppData/Roaming".to_string(),
        "C:/Users/Michael/Saved Games".to_string(),
        "C:/Users/Michael/Documents".to_string(),
        "D:/My Documents".to_string(),
        "C:/Program Files (x86)/Steam/steamapps/common".to_string(),
    ]);

    c.bench_function("find_save_path", |b| {
        b.iter(|| {
            let game_name: String = black_box("Cyberpunk 2077".to_string());
            searcher::find_game_save_path(game_name, dirs_to_check.clone());
        })
    });

    c.bench_function("find_save_path_with_many_paths", |b| {
        b.iter(|| {
            let game_name: String = black_box("Deep Rock Galactic".to_string());
            searcher::find_game_save_path(game_name, dirs_to_check.clone());
        })
    });

    c.bench_function("score_path", |b| {
        b.iter(|| {
            let path: String = black_box(
                "c:/program files (x86)/steam/steamapps/common/deep rock galactic".to_string(),
            );
            searcher::score_path(path);
        })
    });

    c.bench_function("to_alphanumeric", |b| {
        b.iter(|| {
            let string: String = black_box("Batman™: Arkham Knight".to_string());
            searcher::to_alphanumeric(string);
        })
    });
}

criterion_group!(benches, criterion_benchmark);
criterion_main!(benches);
