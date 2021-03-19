from game_save_manager import Backup
import unittest
import os

class TestGameSaveManager(unittest.TestCase):

    test = Backup()


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
        self.assertEqual(self.test.convert_size(os.path.join(os.getcwd(), 'Testing\Folder Example')), '124.0 B')
        self.assertEqual(self.test.convert_size('ValueError'), '0 bits')


    def test_smart_browse(self):
        print('\nTesting smart_browse function')
        game_dict = {
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
        print('\n   Setting up search directories')
        self.test.find_search_directories()
        print('\n   Starting check for each game.')
        for game, path in game_dict.items():
            print(f'   > {game}')
            self.assertEqual(self.test.game_save_location_search(game, test=1), path)


if __name__ == '__main__':
    unittest.main()
