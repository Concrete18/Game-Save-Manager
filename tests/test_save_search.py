from classes.save_finder import SaveFinder
from classes.game import Game
from config.config import Config
from time import sleep
from main import Main  # type: ignore
import unittest


class TestAppIDSearch(unittest.TestCase):
    def test_get_appid(self):
        """
        get_appid
        """
        cfg = Config("config/settings.ini")
        cfg.get_settings()
        tests = {
            "This is not a real game:the sequel": None,
            "Dishonored 2": 403640,
            "Monster Hunter: World": 582010,
            # 'HITMAN™ 2': 863550
        }
        search = SaveFinder(Game, cfg.custom_dirs, debug=0)
        for test_value, answer in tests.items():
            self.assertEqual(search.get_appid(game=test_value), answer)
            sleep(0.5)

    def test_get_appid(self):
        """
        get_appid
        """
        cfg = Config("config/settings.ini")
        cfg.get_settings()
        tests = {
            "This is not a real game:the sequel": None,
            "Dishonored 2": 403640,
            "Monster Hunter: World": 582010,
        }
        search = SaveFinder(Game, cfg.custom_dirs, debug=0)
        for test_value, answer in tests.items():
            self.assertEqual(search.get_appid(game=test_value), answer)
            sleep(0.5)


class TestSmartBrowse(unittest.TestCase):
    def test_all_normal_searches(self):
        """
        Smart Browse
        """
        cfg = Config("config\settings.ini")
        cfg.get_settings()
        search = SaveFinder(Game, cfg.custom_dirs, debug=False)
        game_dict = {
            "Mini Motorways": r"c:/users/michael/appdata/locallow/dinosaur polo club/mini motorways",
            "Phantom Abyss": r"c:/users/michael/appdata/local/phantomabyss/saved",
            "Still There": r"c:/users/michael/appdata/locallow/ghostshark games/still there",
            "Factorio": r"c:/users/michael/appdata/roaming/factorio",
            "Surviving Mars": r"c:/users/michael/appdata/roaming/surviving mars",
            "Wildfire": r"c:/users/michael/appdata/local/wildfire",
            "Teardown": r"c:/users/michael/AppData/local/teardown",
            "Desperados III": r"C:/users/michael/AppData/local/Desperados III",
            "The Forest": r"C:/users/michael/AppData/localLow/SKS/theForest",
            "Manifold Garden": r"C:/users/michael/AppData/localLow/William Chyr Studio/manifold Garden",
            "Valheim": r"C:/users/michael/AppData/localLow/ironGate/valheim",
            "Boneworks": r"C:/users/michael/AppData/localLow/Stress Level Zero/BONEWORKS",
            "Dishonored 2": r"C:/users/michael/Saved Games/Arkane Studios/Dishonored2",
            "Cyberpunk 2077": r"C:/users/michael/Saved Games/cD Projekt Red/cyberpunk 2077",
            "Deep Rock Galactic": r"D:/my Installed Games/Steam Games/steamapps/common/Deep Rock Galactic",
            "Timberborn": r"D:/my Documents/timberborn",
        }
        for game, actual_path in game_dict.items():
            with self.subTest(game=game, actual_path=actual_path):
                found_path = search.find_save_location(game)
                self.assertIn(actual_path.lower(), found_path.lower())

    def test_appid_search(self):
        """
        Smart Browse
        """
        cfg = Config("config\settings.ini")
        cfg.get_settings()
        search = SaveFinder(Game, cfg.custom_dirs, debug=False)
        # test
        found_path = search.find_save_location("HITMAN™ 2")
        actual_path = r"c:/program files (x86)/steam/userdata/22360464/863550"
        self.assertIn(actual_path.lower(), found_path.lower())
