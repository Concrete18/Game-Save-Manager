from classes.logger import Logger
import os, requests, json, re, os, sys, getpass
from time import perf_counter


# WIP finish switch to separate class
class Save_Search(Logger):

    initialdir = "C:/"
    # scoring init
    with open('config\scoring.json') as json_file:
        scoring = json.load(json_file)
    # steam app list init
    app_list = None
    directories_ready = False
    search_directories = []
    
    with open('config\settings.json') as json_file:
        data = json.load(json_file)

        
    def __init__(self, game, debug) -> None:
        '''
        ph
        '''
        self.game = game
        self.debug = debug
        self.drive_letters = self.find__drive_letters()


    def find__drive_letters(self):
        '''
        Finds the active drive letters for storage.
        '''
        with os.popen("fsutil fsinfo drives") as data:
            letter_output = data.readlines()[1]
        words = re.findall('\S+', letter_output)[1:]
        result = []
        for letters in words:
            result.append(letters[0])
        if self.debug:
            print(result)
        return result


    def find_search_directories(self):
        '''
        Finds the directories to use when searching for games.
        '''
        start = perf_counter()
        # os specific settings
        platform = sys.platform
        username = getpass.getuser()
        if platform == 'win32':
            dirs_to_check = [
                rf":/Users/{username}/AppData/Local",
                rf":/Users/{username}/AppData/LocalLow",
                rf":/Users/{username}/AppData/Roaming",
                rf":/Users/{username}/Saved Games",
                rf":/Users/{username}/Documents",
                r":/Program Files (x86)/Steam/steamapps/common",
                r":/Program Files/Steam/steamapps/common"
                ]
        elif platform == 'linux':
            # TODO add linux support to find_search_directories
            dirs_to_check = ['$HOME/.local/share/Steam/userdata']
        # starts directory check
        for dir in dirs_to_check:
            for letter in self.drive_letters:
                current_dir = letter + dir
                if os.path.isdir(current_dir):
                    if 'documents' in current_dir.lower():
                        self.initialdir = current_dir
                    self.search_directories.append(current_dir)
        for custom_saved_dir in self.data['custom_save_directories']:
            self.search_directories.append(custom_saved_dir)
        if self.debug:
            print(self.search_directories)
        finish = perf_counter() # stop time for checking elapsed runtime
        elapsed_time = round(finish-start, 2)
        if self.debug:
            print(f'find_search_directories: {elapsed_time} seconds')
        self.directories_ready = True


    def dir_scoring(self, possible_dir):
        '''
        Uses a scoring system to determines the chance of the given directory to be the save location.
        '''
        # checks if possible_dir is in the blacklist
        dir_blacklist = self.scoring['dir_blacklist']
        for string in dir_blacklist:
            if string.lower() in possible_dir.lower():
                return 0
        # prints possible_dir if debug is 1 and the var is not blank
        if possible_dir != '' and self.debug:
            print(f'\n{possible_dir}')
        current_score = 0
        for found_root, found_dirs, found_files in os.walk(possible_dir, topdown=False):
            for found_file in found_files:
            # file scoring TODO add a way to track scoring that applies
                # + scorers
                for item, score in self.scoring['file_positive_scoring'].items():
                    if item in found_file.lower():
                        current_score += score
                # - scorers
                for item, score in self.scoring['file_negative_scoring'].items():
                    if item in found_file.lower():
                        current_score -= score
            for found_dir in found_dirs:
            # folder scoring
                # + scorers
                for item, score in self.scoring['folder_positive_scoring'].items():
                    if item in found_dir.lower():
                        current_score += score
                # - scorers
                for item, score in self.scoring['folder_negative_scoring'].items():
                    if item in found_dir.lower():
                        current_score -= score
        if self.debug:
            print(f'Score {current_score}')
        return current_score


    def get_app_list(self):
        '''
        Gets the applist from the steam API
        '''
        url = 'http://api.steampowered.com/ISteamApps/GetAppList/v0002/'
        data = requests.get(url)
        if data.status_code == requests.codes.ok:
            return data.json()['applist']['apps']
        else:
            return None


    def get_appid(self, game, app_list):
        '''
        Checks the Steam App list for a game and returns its app id if it exists as entered.
        '''
        if app_list == None:
            app_list = self.get_app_list()
        for item in app_list:
            if item["name"] == game:
                return item['appid']
        return None


    def check_userdata(self, app_id):
        '''
        Checks for a save folder within the steam userdata folder by looking for the given games app_id.
        '''
        existing_paths = []
        if len(self.drive_letters) == 0:
            self.drive_letters = self.find__drive_letters()
        for letter in self.drive_letters:
            path = f'{letter}:/Program Files (x86)/Steam/userdata'
            if os.path.exists(path):
                existing_paths.append(path)
        for path in existing_paths:
            for dirpath, dirnames, filenames in os.walk(path):
                for dir in dirnames:
                    found_path = os.path.join(dirpath, dir)
                    if str(app_id) in found_path:
                        return found_path.replace('/', '\\')
        return False
