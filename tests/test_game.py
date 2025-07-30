# standard library
import re

# local application imports
from utils.game import Game


class TestGame:

    save_path = "C:/Users/John/Saved Games/Arkane/Dishonored2/savegame"
    game = Game(
        name="Dishonored 2",
        save_path=save_path,
        backup_folder="tests/Folder Test",
        prev_backup_hash="45sa456dasd",
        last_backup="2021/07/24 9:56:37",
    )

    def test_Game(self):
        assert self.game.name == "Dishonored 2"
        assert self.game.save_path == self.save_path
        assert self.game.filename == "Dishonored 2"
        assert self.game.backup_path == r"tests/Folder Test\Dishonored 2"
        assert re.search(r"\d+(\.\d+)?\s*(B|KB|MB|GB|TB)", self.game.backup_size)
        assert self.game.last_backup == "2021/07/24 9:56:37"
        assert self.game.prev_backup_hash == "45sa456dasd"

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
        assert self.game.backup_size == "386.0 B"

    def test_is_new_hash(self):
        game = Game(name="Dishonored 2: End of Time", prev_backup_hash="123")
        assert not game.is_new_hash("123")
