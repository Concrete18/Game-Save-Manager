# standard library
import re

# local application imports
from classes.helper import *


class Game:

    def __init__(
        self,
        name: str = "",
        save_location: str = "",
        last_backup: str = "",
        prev_backup_hash: str = "",
        backup_folder: str = "",
    ) -> None:
        self.name = name.strip()
        self.save_location = save_location
        self.last_backup = last_backup
        self.prev_backup_hash = prev_backup_hash
        self.backup_folder = backup_folder
        self.backup_path = os.path.join(self.backup_folder, self.filename)

    def __str__(self) -> str:
        return f'Game("{self.name}", "{self.save_location}")'

    @property
    def filename(self) -> str:
        """
        Removes illegal characters and shortens `name` so it can become a
        valid filename.
        """
        name = re.sub(
            r"[^A-Za-z0-9'(){}\s]+", "", self.name.replace("&", "and")
        ).strip()
        return re.sub(r"\s\s+", " ", name)[0:50]  # removes duplicate spaces and returns

    @property
    def curr_save_hash(self) -> str | None:
        return get_hash(self.save_location)

    @property
    def backup_size(self) -> str:
        return get_dir_size(self.backup_path)
