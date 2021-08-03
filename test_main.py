from main import Main  # type: ignore
from classes.save_search import Save_Search
from classes.game import Game
from time import sleep, perf_counter
import unittest

class TestGameSaveManager(unittest.TestCase):


    def test_smart_browse(self):
        '''
        Smart Browse
        '''
        print('\nTesting smart_browse function')
        main = Main()
        main.debug = 0
        main.output = 0
        search = Save_Search(Game, debug=False)
        game_dict = {
            # 'The Forgotten City':r'C:',
            'HITMAN™ 2': r'C:\Program Files (x86)\Steam\userdata\22360464\863550',
            'Mini Motorways': r'C:\Users\Michael\AppData\LocalLow\Dinosaur Polo Club\Mini Motorways',
            'Phantom Abyss': r'C:\Users\Michael\AppData\Local\PhantomAbyss',
            'Still There': r'C:\Users\Michael\AppData\LocalLow\GhostShark Games\Still There',
            'Factorio': r'C:\Users\Michael\AppData\Roaming\Factorio',
            'Surviving Mars': r'C:\Users\Michael\AppData\Roaming\Surviving Mars',
            'Wildfire': r'C:\Users\Michael\AppData\Local\wildfire',
            'Teardown': r'C:\Users\Michael\AppData\Local\Teardown',
            'Desperados III': r'C:\Users\Michael\AppData\Local\Desperados III',
            'The Forest': r'C:\Users\Michael\AppData\LocalLow\SKS\TheForest',
            'Manifold Garden': r'C:\Users\Michael\AppData\LocalLow\William Chyr Studio\Manifold Garden',
            'Valheim': r'C:\Users\Michael\AppData\LocalLow\IronGate\Valheim',
            'Boneworks': r'C:\Users\Michael\AppData\LocalLow\Stress Level Zero\BONEWORKS',
            'Dishonored 2': r'C:\Users\Michael\Saved Games\Arkane Studios\Dishonored2',
            'Cyberpunk 2077': r'C:\Users\Michael\Saved Games\CD Projekt Red\Cyberpunk 2077',
            'Deep Rock Galactic': r'D:\My Installed Games\Steam Games\steamapps\common\Deep Rock Galactic',
            'Breathedge': r'C:\Program Files (x86)\Steam\steamapps\common\Breathedge',
            'Timberborn': r'D:\My Documents\Timberborn',
            'XCOM 2 War of the Chosen': r'D:\My Documents\My Games\XCOM2 War of the Chosen'}
        print('\n   Setting up search directories')
        search.find_search_directories()
        print('\n   Starting search for each game.')
        elapsed_total = 0
        for game, path in game_dict.items():
            print(f'   > {game}', end="")
            start = perf_counter()
            # self.assertEqual(main.game_save_location_search(game, test=1), path)
            self.assertIn(main.game_save_location_search(game, test=1), path)
            finish = perf_counter()
            elapsed_single = finish-start
            elapsed_total += elapsed_single
            print(f' | {round(elapsed_single, 2)} seconds')
        average = round(elapsed_total/len(game_dict), 2)
        print(f'   Average search time: {average} seconds')
    

if __name__ == '__main__':
    unittest.main()
