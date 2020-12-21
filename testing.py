from GSM import Backup
import unittest
import os


class TestGameSaveManager(unittest.TestCase):


    def test_selected_game_filename(self):
        App = Backup()
        tests = {
        'Amnesia: The Dark Descent':'Amnesia The Dark Descent',
        'Is&this<>correct?':'Isthiscorrect',
        'This is a long test of the file sanitize function':'This is a long test of the file'
        }
        for test_value, answer in tests.items():
            self.assertEqual(App.selected_game_filename(test_value), answer)


    def test_convert_size(self):
        App = Backup()
        self.assertEqual(App.convert_size(os.path.join(os.getcwd(), 'Testing\Folder Example')), '124.0 B')
        self.assertEqual(App.convert_size('ValueError'), '0 bits')


if __name__ == '__main__':
    unittest.main()
