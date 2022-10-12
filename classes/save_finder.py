from classes.logger import Logger
import os, requests, re, os, sys, getpass
import save_search

# TODO rename class
class SaveFinder(Logger):

    # var init
    app_list = None
    initialdir = "C:/"  # TODO check value of below var init

    def __init__(self, game, custom_dirs, debug) -> None:
        """
        Save Search class with game save search methods.
        """
        self.game = game
        self.debug = debug
        self.drive_letters = self.find_drive_letters()
        self.save_dirs = self.find_search_directories() + custom_dirs

    def find_drive_letters(self):
        """
        Finds the active drive letters for storage.
        """
        with os.popen("fsutil fsinfo drives") as data:
            letter_output = data.readlines()[1]
        return [letters[0] for letters in re.findall("\S+", letter_output)[1:]]

    def find_search_directories(self):
        """
        Finds the directories to use when searching for games.
        """
        directories = []
        # os specific settings
        platform = sys.platform
        username = getpass.getuser()
        if platform == "win32":
            dirs_to_check = [
                rf":/Users/{username}/AppData/Local",
                rf":/Users/{username}/AppData/LocalLow",
                rf":/Users/{username}/AppData/Roaming",
                rf":/Users/{username}/Saved Games",
                rf":/Users/{username}/Documents",
                rf":/My Documents",
                r":/Program Files (x86)/Steam/steamapps/common",
                r":/Program Files/Steam/steamapps/common",
            ]
        elif platform == "linux":
            # TODO add linux support to find_search_directories
            dirs_to_check = ["$HOME/.local/share/Steam/userdata"]
        # starts directory check
        for dir in dirs_to_check:
            for letter in self.drive_letters:
                current_dir = letter + dir
                if os.path.isdir(current_dir):
                    if "documents" in current_dir.lower():
                        self.initialdir = current_dir
                    directories.append(current_dir)
        return directories

    def get_app_list(self):
        """
        Gets the applist from the steam API
        """
        url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/?l=english"
        data = requests.get(url)
        if data.status_code == requests.codes.ok:
            return data.json()["applist"]["apps"]
        else:
            return None

    def get_appid(self, game):
        """
        Checks the Steam App list for a `game` and returns its app id if it
        exists as entered. If the app_list has not been populated yet then it
        will be aquired first.
        """
        if self.app_list == None:
            self.app_list = self.get_app_list()
        for item in self.app_list:
            if item["name"] == game:
                return item["appid"]
        return None

    def check_userdata(self, app_id):
        """
        Checks for a save folder within the steam userdata folder by looking
        for the given games `app_id`.
        """
        existing_paths = []
        for letter in self.drive_letters:
            path = f"{letter}:/Program Files (x86)/Steam/userdata"
            if os.path.exists(path):
                existing_paths.append(path)
        for path in existing_paths:
            for dirpath, dirnames, filenames in os.walk(path):
                for dir in dirnames:
                    found_path = os.path.join(dirpath, dir)
                    if str(app_id) in found_path:
                        return found_path
        return False

    def find_save_location(self, full_game_name):
        """
        Runs a Rust version of game save search.
        """
        path = save_search.find_save_path(full_game_name, self.save_dirs)
        # gets possible save location using app id if nothing is found
        if not path:
            appid = self.get_appid(full_game_name)
            path = self.check_userdata(appid).replace("\\", "/")
        if path:
            # gets directory only if path leads to a file
            if os.path.isfile(path):
                return os.path.dirname(path)
            return path
