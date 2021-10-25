from classes.backup import Backup
from classes.game import Game
import unittest

class TestBackup(unittest.TestCase):


    def test_compressed(self):
        print('\nTesting compressed function')
        tests = {
        'Post-Restore Save.zip': True,
        'Post-Restore Save': False,
        'Post-Restore Save.fake': False,
        'Post-Restore Save.tar': True,
        'Post-Restore Save.gztar': True,
        'Post-Restore Save.bztar': True,
        'Post-Restore Save.xztar': True,
        }
        backup = Backup('zip', Game)
        for test_value, answer in tests.items():
            self.assertEqual(backup.compressed(test_value), answer)

    # def test_delete_oldest(self):
    #     print('\nTesting delete_oldest function')
    #     tests = {
    #     'Amnesia: The Dark Descent':'Amnesia The Dark Descent',
    #     'Is&this<>correct?':'Isthiscorrect',
    #     '  This       is  a *&^%^ space *(&^test    ':'This is a space test',
    #     }
    #     for test_value, answer in tests.items():
    #         self.assertEqual(self.game.delete_oldest(test_value), answer)
