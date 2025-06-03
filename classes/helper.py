# standard library
import time, math, os

# third-party imports
from checksumdir import dirhash


def benchmark(func):
    """
    Prints `func` name and its benchmark time.
    """

    def wrapped(*args, **kwargs):
        start = time.perf_counter()
        value = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed = round(end - start, 2)
        print(f"{func.__name__} Completion Time: {elapsed}ms")
        return value

    return wrapped


def get_hash(dir_file: str) -> str | None:
    """
    Gets hash of the given folder.
    """
    if os.path.isdir(dir_file):
        return dirhash(dir_file, "md5")
    return None


def get_dir_size(directory: str) -> str:
    """
    Gets the size of the given `directory` in the best fitting unit of measure.
    """
    total_size = 0
    for path, _, files in os.walk(directory):
        for f in files:
            fp = os.path.join(path, f)
            total_size += os.path.getsize(fp)
    if total_size > 0:
        size_name = ("B", "KB", "MB", "GB", "TB")
        try:
            i = int(math.floor(math.log(total_size, 1024)))
            p = math.pow(1024, i)
            s = round(total_size / p, 2)
            return f"{s} {size_name[i]}"
        except ValueError:
            return "0 bits"
    else:
        return "0 bits"
