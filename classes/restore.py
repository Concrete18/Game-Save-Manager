from classes.logger import Logger
import os, shutil


class Restore(Logger):
    def __init__(self, game, backup) -> None:
        """
        Restore class with restore methods.
        """
        self.game = game
        self.backup = backup

    # TODO move restore tkinter window into this folder

    @staticmethod
    def delete_dir_contents(dir):
        """
        Deletes all files and folders within the given directory.
        """
        for f in os.scandir(dir):
            if os.path.isdir(f):
                shutil.rmtree(f)
            else:
                os.remove(f)

    def decompress(self, file, destination):
        """
        Decompresses the given file into the given destination.
        """
        shutil.unpack_archive(file, destination)
