from game_save_manager import Backup_Class
from time import sleep, perf_counter
import unittest
import os

class TestGameSaveManager(unittest.TestCase):

    test = Backup_Class()


    def test_selected_game_filename(self):
        print('\nTesting selected_game_filename function')
        tests = {
        'Amnesia: The Dark Descent':'Amnesia The Dark Descent',
        'Is&this<>correct?':'Isthiscorrect',
        '  This       is  a *&^%^ space *(&^test    ':'This is a space test',
        }
        for test_value, answer in tests.items():
            self.assertEqual(self.test.get_selected_game_filename(test_value), answer)


    def test_convert_size(self):
        print('\nTesting convert_size function')
        self.assertEqual(self.test.convert_size(os.path.join(os.getcwd(), 'Folder Test\Folder Example')), '124.0 B')
        self.assertEqual(self.test.convert_size('ValueError'), '0 bits')


    def test_compressed(self):
        print('\nTesting compressed function')
        tests = {
        'Post-Restore Save.zip':True,
        'Post-Restore Save':False,
        'Post-Restore Save.fake':False,
        'Post-Restore Save.tar':True,
        'Post-Restore Save.gztar':True,
        'Post-Restore Save.bztar':True,
        'Post-Restore Save.xztar':True,
        }
        for test_value, answer in tests.items():
            self.assertEqual(self.test.compressed(test_value), answer)


    def test_get_appid(self):
        print('\nTesting get_appid function')
        tests = {
        # 'This is not a real game:the sequel':None,
        'Dishonored 2':403640,
        'Monster Hunter: World': 582010
        }
        for test_value, answer in tests.items():
            self.assertEqual(self.test.get_appid(test_value), answer)
            sleep(.5)


    def test_smart_browse(self):
        print('\nTesting smart_browse function')
        game_dict = {
            # 'Barotrauma':r'C:\Users\Michael\AppData\Local\Daedalic Entertainment GmbH\Barotrauma'
            'HITMAN™ 2':r'C:\Program Files (x86)\Steam\userdata\22360464\863550',
            'Monster Hunter: World':r'C:\Program Files (x86)\Steam\userdata\22360464\582010',
            'Phantom Abyss':r'C:\Users\Michael\AppData\Local\PhantomAbyss',
            'Still There':r'C:\Users\Michael\AppData\LocalLow\GhostShark Games\Still There',
            'Factorio':r'C:\Users\Michael\AppData\Roaming\Factorio',
            'Surviving Mars':r'C:\Users\Michael\AppData\Roaming\Surviving Mars',
            'Wildfire':r'C:\Users\Michael\AppData\Local\wildfire',
            'Teardown':r'C:\Users\Michael\AppData\Local\Teardown',
            'Desperados III':r'C:\Users\Michael\AppData\Local\Desperados III',
            'The Forest':r'C:\Users\Michael\AppData\LocalLow\SKS\TheForest',
            'Manifold Garden':r'C:\Users\Michael\AppData\LocalLow\William Chyr Studio\Manifold Garden',
            'Valheim':r'C:\Users\Michael\AppData\LocalLow\IronGate\Valheim',
            'Boneworks':r'C:\Users\Michael\AppData\LocalLow\Stress Level Zero\BONEWORKS',
            'Dishonored 2':r'C:\Users\Michael\Saved Games\Arkane Studios\Dishonored2',
            'Cyberpunk 2077':r'C:\Users\Michael\Saved Games\CD Projekt Red\Cyberpunk 2077',
            'Deep Rock Galactic':r'D:\My Installed Games\Steam Games\steamapps\common\Deep Rock Galactic',
            'Breathedge':r'C:\Program Files (x86)\Steam\steamapps\common\Breathedge',
            'Timberborn':r'D:\My Documents\Timberborn',
            'XCOM 2 War of the Chosen':r'D:\My Documents\My Games\XCOM2 War of the Chosen'}
        self.test.debug = 0
        self.test.output = 0
        print('\n   Setting up search directories')
        self.test.find_search_directories()
        print('\n   Starting search for each game.')
        elapsed_total = 0
        for game, path in game_dict.items():
            print(f'    > {game}', end="")
            start = perf_counter()
            self.assertEqual(self.test.game_save_location_search(game, test=1), path)
            finish = perf_counter()
            elapsed_single = finish-start
            elapsed_total += elapsed_single
            print(f' | {round(elapsed_single, 2)} seconds')
        average = round(elapsed_total/len(game_dict), 2)
        print(f'   Average search time: {average} seconds')


if __name__ == '__main__':
    unittest.main()
