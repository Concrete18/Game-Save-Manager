from classes.helper import Helper
import unittest


class TestBackup(unittest.TestCase):
    def test_get_hash(self):
        print("\n", "Testing get_hash function")
        test = Helper()
        tests = {
            "test/Folder Test/Folder Example": "c391af98a15c45425f1cd3d7714d0354",
        }
        for test_value, answer in tests.items():
            self.assertEqual(test.get_hash(test_value), answer)
