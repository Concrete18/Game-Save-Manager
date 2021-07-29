from classes.logger import Logger
from time import sleep, perf_counter
import os, requests
# optional imports
try:
    import requests
    requests_installed = 1
except ModuleNotFoundError:
    requests_installed = 0


# WIP finish switch to separate class
class Save_Search(Logger):

    initialdir = "C:/"

        
    def __init__(self, game, debug) -> None:
        '''
        ph
        '''
        self.game = game
        self.debug = debug


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


    def get_appid(self, game):
        '''
        Checks the Steam App list for a game and returns its app id if it exists as entered.
        '''
        if self.applist == None:
            applist = 'http://api.steampowered.com/ISteamApps/GetAppList/v0002/'
            data = requests.get(applist)
            if data.status_code != requests.codes.ok:
                return None
            self.applist = data.json()['applist']['apps']
        for item in self.applist:
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


    def game_save_location_search(self, full_game_name, test=0):
        '''
        Searches for possible save game locations for the given name using a point based system.
        The highes scoring directory is chosen.
        '''
        # TODO split into more functions
        # var setup
        overall_start = perf_counter() # start time for checking elapsed runtime
        best_score = 0
        dir_changed = 0
        current_score = 0
        possible_dir = ''
        search_method = 'name search'
        self.best_dir = self.initialdir
        if self.debug:
            print(f'\nGame: {self.game.filename}')
        # waits for search directories to be ready before the save search is started
        while self.search_directories_incomplete:
            sleep(.1)
        # disables progress bar actions when testing
        if test == 0:
            self.progress['maximum'] = len(self.search_directories) + 1
        for directory in self.search_directories:
            if self.debug:
                print(f'\nCurrent Search Directory: {directory}')
            directory_start = perf_counter()
            for root, dirs, files in os.walk(directory, topdown=False):
                for dir in dirs:
                    if self.game.get_filename(full_game_name).lower().replace(' ', '') in dir.lower().replace(' ', ''):
                        possible_dir = os.path.join(root, dir)
                        current_score = self.dir_scoring(possible_dir)
            # update based on high score
            directory_finish = perf_counter()
            if self.debug:
                print(f'Dir Search Time: {round(directory_finish-directory_start, 2)} seconds')
            # disables progress bar actions when testing
            if test == 0:
                self.progress['value'] += 1
            if current_score > best_score:
                best_score = current_score
                self.best_dir = os.path.abspath(possible_dir)
                # early break if threshold is met
                if current_score > 600:
                    break
            current_score = 0
        overall_finish = perf_counter() # stop time for checking elapsed runtime
        elapsed_time = round(overall_finish-overall_start, 2)
        if self.debug:
            print(f'\n{self.game.filename}\nOverall Search Time: {elapsed_time} seconds')
            print(f'Path Used: {self.best_dir}')
            print(f'Path Score: {best_score}')
        # checks if nothing was found from the first search
        if self.best_dir == self.initialdir:
            if requests_installed:
                app_id = self.get_appid(full_game_name)
                if app_id != None:
                    app_id_path = self.check_userdata(app_id)
                    if app_id_path is not False:
                        self.best_dir = app_id_path
                        search_method = 'app id search'
                    else:
                        self.logger.info(f'No Game save can be found for {full_game_name}')
                else:
                    self.logger.info(f'app_id cant be found for {full_game_name}')
        if test == 0:
            game_save = os.path.abspath(self.GameSaveEntry.get())
            if game_save != self.script_dir:
                if self.best_dir in game_save:
                    print('Found save is correct.')
                else:
                    print('Found save is incorrect.')
                    dir_changed = 1
        else:
            return self.best_dir
        self.progress['value'] = self.progress['maximum']
        # completion time output
        limit = 50
        if len(self.best_dir) > limit:
            info = f'Path Found in {elapsed_time} seconds\n...{self.best_dir[-limit:]}'
        else:
            info = f'Path Found in {elapsed_time} seconds\n{self.best_dir[-limit:]}'
        self.logger.info(f'Save for "{full_game_name}" found in {elapsed_time} seconds via {search_method}.')
        self.info_label.config(text=info)
        self.completion_sound()
        # enables the browse button when a save folder seems to be found
        if self.best_dir != self.initialdir:
            if dir_changed:
                # adds info that the found save location is not the same as the save location in the entry box
                info += f'\nFound directory is different then entered directory.'
            self.s_browse.config(state='normal')
        else:
            pass
