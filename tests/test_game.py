# standard library
import re

# local application imports
from classes.game import Game
from classes.database import Database


class TestGame:

    backup_path = "tests/Folder Test"
    db_loc = "tests/testing.db"

    def test_get(self):
        database = Database(self.backup_path, self.db_loc)
        game = database.get("Dishonored 2")
        assert game.name == "Dishonored 2"
        save_location = (
            r"C:\Users\Michael\Saved Games\Arkane Studios\Dishonored2\base\savegame"
        )
        assert game.save_location == save_location
        assert game.filename == "Dishonored 2"
        assert game.backup_path == r"tests/Folder Test\Dishonored 2"
        assert re.search(r"\d+(\.\d+)?\s*(B|KB|MB|GB|TB)", "386.0 B")
        assert game.last_backup == "2021/07/24 9:56:37"
        assert game.prev_backup_hash == "45sa456dasd"

    def test_get_filename(self):
        tests = {
            "Amnesia: The Dark Descent": "Amnesia The Dark Descent",
            "Is&this<>correct?": "Isandthiscorrect",
            "  This       is  a *^%^ space *^test    ": "This is a space test",
        }
        for test_value, answer in tests.items():
            game = Game(name=test_value)
            assert game.filename == answer

    def test_convert_size(self):
        database = Database(self.backup_path, self.db_loc)
        game = database.get("Dishonored 2")

        assert game.backup_size == "386.0 B"
