from classes.logger import Logger
from zipfile import ZipFile
import os, shutil


class Backup(Logger):
    def __init__(self, game, compression_type) -> None:
        """
        Backup class with save backup methods.
        """
        self.game = game
        self.compression_type = compression_type

    def compress(self, file_path, game_backup_loc, file_name):
        """
        Compresses the `file_path` into the `destination` path.
        """
        destination = os.path.join(game_backup_loc, file_name)
        if os.path.isdir(file_path):
            shutil.make_archive(
                base_name=destination, format=self.compression_type, root_dir=file_path
            )
        elif os.path.isfile(file_path):
            if not os.path.exists(game_backup_loc):
                os.mkdir(game_backup_loc)
            try:
                # with ZipFile(destination + '.zip', 'w') as zipf:
                #     zipf.write(file_path, arcname=file_name)
                print(os.path.dirname(file_path))
                os.chdir(os.path.dirname(file_path))
                ZipFile(destination + ".zip", mode="w").write(file_path)
                os.chdir(os.path.dirname(os.path.abspath(__file__)))
            except PermissionError:
                print("failed due to permission error")
                print("destination", destination)
                print("file_path", file_path)
                print(os.path.exists(destination))

    def delete_oldest(self, game_name, path, redundancy, ignore):
        """
        Deletes the oldest saves within the given `path` so only the newest specified amount (`redundancy`) is left.

        If the value of `ignore` is in the filename then it will be ignored during this process.
        """
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
                        self.logger.warn(
                            f"Failed to delete oldest save for {game_name} due to permission error."
                        )
                        # tries to delete the folder again if it managed to delete the contents only
                        try:
                            os.rmdir(file_to_delete)
                        except PermissionError:
                            self.logger.warn(
                                f"Failed to delete empty folder for {game_name} due to permission error."
                            )
                else:
                    os.remove(file_to_delete)
            self.logger.info(
                f"{game_name} had more then {redundancy} Saves. Deleted oldest saves."
            )
