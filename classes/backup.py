from classes.logger import Logger
import os, shutil

class Backup(Logger):

    
    def __init__(self, compression_type, game) -> None:
        '''
        ph
        '''
        self.compression_type = compression_type
        self.game = game


    def compress(self, file_path, destination):
        '''
        Compresses the file given as the file path into the destination path.
        '''
        shutil.make_archive(base_name=destination, format=self.compression_type, root_dir=file_path)


    def decompress(self,file, destination):
        '''
        Decompresses the given file into the given destination.
        '''
        shutil.unpack_archive(file, destination)


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


    def backup_orignal_save(self, selected_backup, full_save_path):
        '''
        Unpacks or copies the backup depending on if it is compressed or not
        '''
        # checks if the backup is compressed
        if self.compressed(selected_backup.name):
            self.decompress(selected_backup.path, self.game.save_location)
            self.logger.info(f'Restored save for {self.game.name} from compressed backup.')
        else:
            if os.path.exists(self.game.save_location):
                print('Path already exists.')
                # BUG FileExistsError: [WinError 183] Cannot create a file when that file already exists: 
                # 'D:\\My Documents\\Shadow of the Tomb Raider\\76561197982626192'
            shutil.copytree(full_save_path, self.game.save_location)
            self.logger.info(f'Restored save for {self.game.name}from backup.')
