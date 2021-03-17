from game_save_manager import Backup
import unittest
import os


class TestGameSaveManager(unittest.TestCase):

    print('Starting Test')


    def test_selected_game_filename(self):
        print('\nTesting selected_game_filename function')
        tests = {
        'Amnesia: The Dark Descent':'Amnesia The Dark Descent',
        'Is&this<>correct?':'Isthiscorrect',
        '  This       is  a *&^%^ space *(&^test    ':'This is a space test',
        }
        for test_value, answer in tests.items():
            print(answer)
            self.assertEqual(Backup.get_selected_game_filename(test_value), answer)


    def test_convert_size(self):
        print('\nTesting convert_size function')
        self.assertEqual(Backup.convert_size(os.path.join(os.getcwd(), 'Testing\Folder Example')), '124.0 B')
        self.assertEqual(Backup.convert_size('ValueError'), '0 bits')


    def test_smart_browse(self):
        print('\nTesting smart_browse function')
        game_dict = {
            'Teardown':r'C:\Users\Michael\AppData\Local\Teardown',
            'Manifold Garden':r'C:\Users\Michael\AppData\LocalLow\William Chyr Studio\Manifold Garden',
            'Deep Rock Galactic':r'D:\My Installed Games\Steam Games\steamapps\common\Deep Rock Galactic',
            'Breathedge':r'C:\Program Files (x86)\Steam\steamapps\common\Breathedge',
            'Surviving Mars':r'C:\Users\Michael\AppData\Roaming\Surviving Mars',
            'Valheim':r'C:\Users\Michael\AppData\LocalLow\IronGate\Valheim',
            'Timberborn':r'D:\My Documents\Timberborn',
            'Cyberpunk 2077':r'C:\Users\Michael\Saved Games\CD Projekt Red\Cyberpunk 2077',
            'Boneworks':r'C:\Users\Michael\AppData\LocalLow\Stress Level Zero\BONEWORKS',
            'Factorio':r'C:\Users\Michael\AppData\Roaming\Factorio',
            'Desperados III':r'C:\Users\Michael\AppData\Local\Desperados III'}

        Backup.debug = 0
        print('\nSetting up search directories')
        Backup.find_search_directories(test=1)
        print('\nStarting check for each game.')
        for game, path in game_dict.items():
            print(game)
            self.assertEqual(Backup.smart_browse(game), path)


if __name__ == '__main__':
    unittest.main()
