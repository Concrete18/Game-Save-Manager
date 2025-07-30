# standard library
import re

# local application imports
from utils.database import Database


class TestDatabase:

    backup_path = "tests/Folder Test"
    db_loc = "tests/testing.db"

    def test_get(self):
        database = Database(self.backup_path, self.db_loc)
        game = database.get("Dishonored 2")
        assert game.name == "Dishonored 2"
        save_path = (
            r"C:\Users\Michael\Saved Games\Arkane Studios\Dishonored2\base\savegame"
        )
        assert game.save_path == save_path
        assert game.filename == "Dishonored 2"
        assert game.backup_path == r"tests/Folder Test\Dishonored 2"
        assert re.search(r"\d+(\.\d+)?\s*(B|KB|MB|GB|TB)", "386.0 B")
        assert game.last_backup == "2021/07/24 9:56:37"
        assert game.prev_backup_hash == "45sa456dasd"
