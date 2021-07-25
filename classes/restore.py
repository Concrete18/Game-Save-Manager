from classes.logger import Logger
import os, shutil

class Restore(Logger):

    
    def __init__(self, game) -> None:
        '''
        ph
        '''
        self.game = game
    

    # TODO move restore tkinter window into this folder


    def delete_dir_contents(dir):
        '''
        Deletes all files and folders within the given directory.
        '''
        for f in os.scandir(dir):
            if os.path.isdir(f):
                shutil.rmtree(f)
            else:
                os.remove(f)


    def decompress(self,file, destination):
        '''
        Decompresses the given file into the given destination.
        '''
        shutil.unpack_archive(file, destination)


    def backup_orignal_save(self, selected_backup, full_save_path):
        '''
        Unpacks or copies the backup depending on if it is compressed or not
        '''
        # checks if the backup is compressed
        if self.game.compressed(selected_backup.name):
            self.decompress(selected_backup.path, self.game.save_location)
            self.logger.info(f'Restored save for {self.game.name} from compressed backup.')
        else:
            if os.path.exists(self.game.save_location):
                print('Path already exists.')
                # BUG FileExistsError: [WinError 183] Cannot create a file when that file already exists: 
                # 'D:\\My Documents\\Shadow of the Tomb Raider\\76561197982626192'
            shutil.copytree(full_save_path, self.game.save_location)
            self.logger.info(f'Restored save for {self.game.name}from backup.')
