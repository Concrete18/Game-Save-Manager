from classes.game import Game
import unittest

class TestGame(unittest.TestCase):

    backup_path = 'Save Backup'
    db_loc = 'test\\testing.db'

    def test_set(self):
        game = Game(self.backup_path, self.db_loc)
        print('\nTesting Game.get method')
        game.set('Dishonored 2')
        self.assertEqual(game.name, 'Dishonored 2')
        save_location = r'C:\Users\Michael\Saved Games\Arkane Studios\Dishonored2\base\savegame'
        self.assertEqual(game.save_location, save_location)
        self.assertEqual(game.filename, 'Dishonored 2')
        self.assertEqual(game.backup_loc, 'Save Backup\Dishonored 2')
        self.assertRegex(game.backup_size, r'[. 0-9]+(B|KB|MB|GB|TB)')
        self.assertEqual(game.last_backup, '2021/07/24 9:56:37')

    def test_get_filename(self):
        print('\nTesting get_filename function')
        tests = {
        'Amnesia: The Dark Descent':'Amnesia The Dark Descent',
        'Is&this<>correct?':'Isandthiscorrect',
        '  This       is  a *^%^ space *(^test    ':'This is a space test',
        }
        game = Game(self.backup_path, self.db_loc)
        for test_value, answer in tests.items():
            self.assertEqual(game.get_filename(test_value), answer)

    def test_convert_size(self):
        print('\nTesting get_dir_size function')
        main = Game(self.backup_path, self.db_loc)
        self.assertEqual(main.get_dir_size('test\Folder Test\Folder Example'), '124.0 B')
        self.assertEqual(main.get_dir_size('ValueError'), '0 bits')

    def test_database_check(self):
        print('\nTesting database_check function')
        game = Game(self.backup_path, self.db_loc)
        self.assertEqual(game.database_check(), [])
