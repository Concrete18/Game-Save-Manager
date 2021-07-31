from classes.save_search import Save_Search
from classes.game import Game
import unittest

class TestBackup(unittest.TestCase):


    def test_game_save_location_search(self):
        '''
        Game Save Search
        '''
        main = Save_Search(Game, 1)
        path = r'C:\Users\Michael\AppData\Local\Teardown'
        main.game.set('Teardown')
        self.assertIn(main.game_save_location_search('Teardown', test=1), path)


if __name__ == '__main__':
    unittest.main()
