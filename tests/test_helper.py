from classes.helper import *


class TestBackup:
    def test_get_hash(self):
        path = "tests/Folder Test/Folder Example"
        assert get_hash(path) == "c391af98a15c45425f1cd3d7714d0354"
