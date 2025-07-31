# standard library
import re

# local application imports
from utils.utils import *


class Game:

    def __init__(
        self,
        name: str = "",
        save_path: str = "",
        last_backup: str = "",
        prev_backup_hash: str = "",
        backup_folder: str = "",
    ) -> None:
        self.name = name.strip()
        self.save_path = save_path
        self.last_backup = last_backup
        self.prev_backup_hash = prev_backup_hash
        self.backup_folder = backup_folder

    def __str__(self) -> str:
        return f'Game("{self.name}", "{self.save_path}")'

    def __bool__(self) -> bool:
        return bool(self.name)

    @property
    def filename(self) -> str:
        """
        Removes illegal characters and shortens `name` so it can become a valid filename.
        """
        # removes illegal characters
        name = re.sub(
            r"[^A-Za-z0-9'(){}\s]+", "", self.name.replace("&", "and")
        ).strip()
        # removes duplicate spaces
        return re.sub(r"\s\s+", " ", name)[0:50]

    @property
    def backup_path(self) -> str:
        return os.path.join(self.backup_folder, self.filename)

    @property
    def curr_save_hash(self) -> str | None:
        return get_hash(self.save_path)

    @property
    def backup_size(self) -> str:
        return get_dir_size(self.backup_path)

    def is_new_hash(self, new_hash: str | None) -> bool:
        """
        Returns True if old hash and `new_hash` are not identical.
        """
        if not isinstance(new_hash, str):
            print("New hash is invalid")
            raise (TypeError)
        if not isinstance(self.prev_backup_hash, str):
            print("Previous hash does not exist")
            return True
        return new_hash != self.prev_backup_hash

    def save_path_exists(self):
        return os.path.exists(self.save_path)

    def backup_path_exists(self):
        return os.path.exists(self.backup_path)
