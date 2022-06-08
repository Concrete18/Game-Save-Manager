from checksumdir import dirhash
import time, os


class Helper:
    def benchmark(func):
        """
        Prints `func` name and its benchmark time.
        """

        def wrapped(*args, **kwargs):
            start = time.perf_counter()
            value = func(*args, **kwargs)
            end = time.perf_counter()
            elapsed = round(end - start, 2)
            print(f"{func.__name__} Completion Time: {elapsed}")
            return value

        return wrapped

    def get_hash(self, dir_file):
        """
        Gets hash of the given file or folder.
        """
        if os.path.isdir(dir_file):
            return dirhash(dir_file, "md5")
        else:
            return self.hash_file(dir_file)
