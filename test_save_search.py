from classes.save_search import Save_Search
from classes.game import Game
from time import sleep
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
        'Monster Hunter: World': 582010
        }
        search = Save_Search(Game, debug=0)
        for test_value, answer in tests.items():
            self.assertEqual(search.get_appid(game=test_value), answer)
            sleep(.5)


    # def test_game_save_location_search(self):
    #     '''
    #     Game Save Search
    #     '''
    #     main = Save_Search(Game, 1)
    #     path = r'C:\Users\Michael\AppData\Local\Teardown'
    #     main.game.set('Teardown')
    #     self.assertIn(main.game_save_location_search('Teardown', test=1), path)


if __name__ == '__main__':
    unittest.main()
