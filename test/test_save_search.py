from classes.save_search import Save_Search
from classes.game import Game
from time import sleep
from main import Main # type: ignore
import unittest

class TestBackup(unittest.TestCase):


    def test_get_appid(self):
        '''
        get_appid
        '''
        print('\nTesting get_appid function')
        tests = {
        'This is not a real game:the sequel': None,
        'Dishonored 2': 403640,
        'Monster Hunter: World': 582010,
        # 'HITMAN™ 2': 863550
        }
        search = Save_Search(Game, debug=0)
        for test_value, answer in tests.items():
            self.assertEqual(search.get_appid(game=test_value), answer)
            sleep(.5)
