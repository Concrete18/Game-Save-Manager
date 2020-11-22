from unittest.mock import patch
from GSM import Backup
import unittest
import os


class TestAFC(unittest.TestCase):


    def test_Sanitize_For_Filename(self):
        App = Backup()
        tests = {
        'Amnesia: The Dark Descent':'Amnesia The Dark Descent',
        'Is&this<>correct?':'Isthiscorrect',
        'This is a long test of the file sanitize function':'This is a long test of the file'
        }
        for test, answer in tests.items():
            self.assertEqual(App.Sanitize_For_Filename(test), answer)


    def test_Convert_Size(self):
        App = Backup()
        self.assertEqual(App.Convert_Size(os.path.join(os.getcwd(), 'Testing\Folder Example')), '124.0 B')
        self.assertEqual(App.Convert_Size('ValueError'), '0 bits')


if __name__ == '__main__':
    unittest.main()
