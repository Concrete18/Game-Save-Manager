# standard library
import time, math, os
import datetime as dt

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


def readable_time_since(
    since_date: dt.datetime | str, checked_date: dt.datetime | None = None
) -> str:
    """
    Converts into time since for the given datetime object given
    as `since_date`.

    Examples:

    1.2 seconds ago | 3.4 minutes ago | 5.6 hours ago | 7.8 days ago
    | 9.1 months ago | 10.1 years ago

    `since_date`: Past date
    `checked_date`: Current or more recent date (Optional) defaults to
    current date if not given.
    """
    if not checked_date:
        checked_date = dt.datetime.now()
    if type(since_date) == str:
        since_date = dt.datetime.strptime(since_date, "%Y/%m/%d %H:%M:%S")
    if not isinstance(since_date, dt.datetime):
        raise Exception("Incorrect since_date given")
    seconds = (
        checked_date - since_date
    ).total_seconds()  # converts datetime object into seconds
    if seconds <= 0:
        raise Exception(
            "Invalid Response - since_date takes place after the checked date."
        )
    minutes = seconds / 60  # seconds in a minute
    hours = seconds / 3600  # minutes in a hour
    days = seconds / 86400  # hours in a day
    months = seconds / (30 * 24 * 60 * 60)  # days in an average month rounded down
    years = seconds / dt.timedelta(days=365).total_seconds()  # months in a year
    if years >= 1:
        s = "" if round(years, 2) == 1 else "s"
        return f"{round(years, 1)} year{s} ago"
    if months >= 1:
        s = "" if months == 1 else "s"
        return f"{round(months, 1)} month{s} ago"
    if days >= 1:
        s = "" if days == 1 else "s"
        return f"{round(days, 1)} day{s} ago"
    if hours >= 1:
        s = "" if hours == 1 else "s"
        return f"{round(hours, 1)} hour{s} ago"
    if minutes >= 1:
        s = "" if minutes == 1 else "s"
        return f"{round(minutes, 1)} minute{s} ago"
    else:
        return f"{round(seconds, 1)} seconds ago"
