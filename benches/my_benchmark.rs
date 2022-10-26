use criterion::{black_box, criterion_group, criterion_main, Criterion};

use save_searcher::{find_save_path, to_alphanumeric};

fn criterion_benchmark(c: &mut Criterion) {
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
    c.bench_function("find_save_path", |b| {
        b.iter(|| {
            find_save_path(
                black_box("Cyberpunk 2077".to_string()),
                black_box(dirs_to_check.clone()),
            )
            .unwrap();
        })
    });

    c.bench_function("to_alphanumeric", |b| {
        b.iter(|| {
            to_alphanumeric(black_box("Batman™: Arkham Knight".to_string()));
        })
    });
}

criterion_group!(benches, criterion_benchmark);
criterion_main!(benches);
