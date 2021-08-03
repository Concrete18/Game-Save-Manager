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
        Returns True if the file is compressed with a valid compression type.
        '''
        available_compression = []
        for item in shutil.get_archive_formats():
            available_compression.append(f'.{item[0]}')
        filetype = os.path.splitext(file)[1]
        if filetype in available_compression:
            return True
        else:
            return False


    def compress(self, file_path, destination):
        '''
        Compresses the file given as the file path into the destination path.
        '''
        shutil.make_archive(base_name=destination, format=self.compression_type, root_dir=file_path)


    def delete_oldest(self, path, redundancy, ignore):
        '''
        Deletes the oldest saves so only the newest specified amount is left.

        Arguments:

        game -- name of folder that will have all but the newest saves deleted
        '''
        # creates save list
        saves_list = []
        for file in os.scandir(path):
            # ignores pre restore backup
            if ignore not in file.name:
                saves_list.append(file.path)
        # exits if the save list is shorted then the backup_redundancy
        if len(saves_list) <= redundancy:
            return
        else:
            sorted_list = sorted(saves_list, key=os.path.getctime, reverse=True)
            for i in range(redundancy, len(saves_list)):
                if os.path.isdir(sorted_list[i]):
                    shutil.rmtree(sorted_list[i])
                else:
                    os.remove(sorted_list[i])
            self.logger.info(f'{self.game.name} had more then {redundancy} Saves. Deleted oldest saves.')
