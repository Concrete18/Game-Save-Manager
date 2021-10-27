from classes.logger import Logger
import os, shutil


class Backup(Logger):

    
    def __init__(self, game, compression_type) -> None:
        '''
        Backup class with save backup methods.
        '''
        self.game = game
        self.compression_type = compression_type


    def compressed(self, file):
        '''
        Returns True if the `file` is compressed with a valid compression type.
        '''
        available_compression = [f'.{item[0]}' for item in shutil.get_archive_formats()]
        filetype = os.path.splitext(file)[1]
        if filetype in available_compression:
            return True
        else:
            return False

    def compress(self, file_path, destination):
        '''
        Compresses the `file_path` into the `destination` path.
        '''
        shutil.make_archive(base_name=destination, format=self.compression_type, root_dir=file_path)

    def delete_oldest(self, path, redundancy, ignore):
        '''
        Deletes the oldest saves within the given `path` so only the newest specified amount (`redundancy`) is left.

        If the value of `ignore` is in the filename then it will be ignored during this process.
        '''
        # creates save list
        saves_list = [file.path for file in os.scandir(path) if ignore not in file.name]
        # exits if the save list is shorted then the backup_redundancy
        if len(saves_list) <= redundancy:
            return
        else:
            sorted_list = sorted(saves_list, key=os.path.getctime, reverse=True)
            for i in range(redundancy, len(saves_list)):
                file_to_delete = sorted_list[i]
                if os.path.isdir(sorted_list[i]):
                    try:
                        shutil.rmtree(file_to_delete)
                    except PermissionError:
                        self.logger.warn(f'Failed to delete oldest saves for {self.game.name} due to permission error.')
                        # tries to delete the folder again if it managed to delete the contents only
                        os.rmdir(file_to_delete)
                else:
                    os.remove(file_to_delete)
            self.logger.info(f'{self.game.name} had more then {redundancy} Saves. Deleted oldest saves.')
