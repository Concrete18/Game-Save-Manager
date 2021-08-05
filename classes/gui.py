import shutil, json, os, sys, subprocess, winsound
from time import sleep, perf_counter
from threading import Thread
import datetime as dt
from tkinter import ttk, filedialog, messagebox
import tkinter as Tk

# classes
from classes.logger import Logger


main_gui = Tk.Tk()


class GUI(Logger):

    # var init
    title = 'Game Save Manager'
    allowed_filename_characters = '[^a-zA-Z0-9.,\s]'
    backup_restore_in_progress = False
    default_entry_value = 'Type Search Query Here'
    post_save_name = 'Post-Restore Save'


    def __ini__(self):
        '''
        ph
        '''
        self.main_gui = Tk.Tk()
        self.main_gui.protocol("WM_DELETE_WINDOW", self.exit_program)
        window_width = 680
        window_height = 550
        self.tk_window_options(self.main_gui, window_width, window_height)
        # self.main_gui.geometry(f'{window_width}x{window_height}+{width}+{height}')


    def backup_dest_check(self):
        '''
        Checks if backup destination in settings exists and asks if you want to choose one if it does not.
        '''
        Tk.Tk().withdraw()
        if not os.path.exists(self.backup_dest):
            msg = 'Do you want to choose a save backup directory instead of using a default within the program folder?'
            response = messagebox.askyesno(title=self.title, message=msg)
            if response:
                self.backup_dest = filedialog.askdirectory(initialdir="C:/", title="Select Save Backup Directory")
                if os.path.exists(self.backup_dest):
                    self.data['settings']['backup_dest'] = self.backup_dest
                    json_object = json.dumps(self.data, indent = 4)  # Serializing json
                    with open('config\settings.json', "w") as outfile:  # Writing to sample.json
                        outfile.write(json_object)
                else:
                    messagebox.showwarning(title=self.title, message='Path does not exist.')
            else:
                os.mkdir(self.backup_dest)


    def run_full_backup(self):
        '''
        Backups up the game entered based on SQLite save location data to the specified backup folder.
        '''

        def backup():
            '''
            Runs a single backup for the entered arg.
            Also sets self.backup_restore_in_progress to True so the program wont quick during a backup.
            '''
            self.backup_restore_in_progress = True
            current_time = dt.datetime.now().strftime("%m-%d-%y %H-%M-%S")
            dest = os.path.join(self.game.backup_loc, current_time)
            if self.enable_compression:
                self.backup.compress(self.game.save_location, dest)
            else:
                shutil.copytree(self.game.save_location, dest)
            self.backup.delete_oldest(self.game.backup_loc, self.backup_redundancy, self.post_save_name)
            sleep(.3)
            # BUG total_size is wrong for some games right after it finishes backing up
            self.game.get_backup_size()
            total_backups = len(os.listdir(self.game.backup_loc))
            info = f'{self.game.name} has been backed up.\n'\
                f'Game Backup Size: {self.game.backup_size} from {total_backups} backups'
            self.ActionInfo.config(text=info)
            # BUG repeated presses replaces the wrong entry
            self.game_listbox.delete(Tk.ACTIVE)
            self.game_listbox.insert(0, self.game.name)
            self.logger.info(f'Backed up Save for {self.game.name}.')
            self.backup_restore_in_progress = False
            self.completion_sound()
        if self.game.name == None:
            messagebox.showwarning(title=self.title, message='No game is selected yet.')
            return
        self.ActionInfo.config(text=f'Backing up {self.game.name}\nDo not close program.')
        try:
            Thread(target=backup).start()
            last_backup = dt.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
            self.game.update_last_backup(self.game.name, last_backup)
        except FileNotFoundError:
            messagebox.showwarning(title=self.title,  message='Action Failed - File location does not exist.')
            self.logger.error(f'Failed to Backed up Save for {self.game.name}. File location does not exist.')
        except FileExistsError:
            messagebox.showwarning(title=self.title, message='Action Failed - Save Already Backed up.')
            self.logger.error(f'Failed to Backed up Save for {self.game.name}. Save Already Backed up.')
        except SystemExit:
            print('Cancelled Backup.')


    def tk_window_options(self, window_name, window_width, window_height, define_size=0):
        '''
        Disables window resize and centers window if config enables each.
        '''
        window_name.title(self.title)
        if sys.platform == 'win32':
            window_name.iconbitmap(window_name, 'images\Save_icon.ico')
        if self.disable_resize:  # sets window to not resize if disable_resize is set to 1
            window_name.resizable(width=False, height=False)
        if self.center_window == 1:
            width_pos = int((window_name.winfo_screenwidth()-window_width)/2)
            height_pos = int((window_name.winfo_screenheight()-window_height)/2)
            if define_size:
                window_name.geometry(f'{window_width}x{window_height}+{width_pos}+{height_pos}')
            else:
                window_name.geometry(f'+{width_pos}+{height_pos}')


    def backup_shortcut(self, event):
        '''
        Shortcut that activates when pressing enter while a game is selected.
        '''
        response = messagebox.askquestion(
            title=self.title,
            message=f'Are you sure you want to backup {self.game.name}')
        if response == 'yes':
            self.run_full_backup()
        else:
            self.game_listbox.activate(0)
            return
        print(event)


    def restore_save(self):
        '''
        Opens an interface for picking the dated backup of the selected game to restore.

        First it checks if an existing save exists or if a game is even selected(Exits function if no game is selected).
        '''
        # TODO test Restore functions
        # exits if no game is selected
        if self.game.name == None:
            messagebox.showwarning(title=self.title, message='No game is selected yet.')
            return
        self.backup_restore_in_progress = True  # disables closing the interface until restore completes
        # checks if the game has a backup folder
        if os.path.exists(self.game.backup_loc):
            # creates list of backups that can be restored
            self.save_dic = {}
            for file in os.scandir(self.game.backup_loc):
                file_name = os.path.splitext(file.name)[0]
                if file_name == self.post_save_name:
                    self.save_dic['Undo Last Restore'] = file
                    continue
                try:
                    updated_name = dt.datetime.strptime(file_name, '%m-%d-%y %H-%M-%S').strftime('%b %d, %Y %I:%M %p')
                except ValueError:
                    updated_name = file_name
                self.save_dic[updated_name] = file
        else:
            # brings up a warning if no backup exists for the selected game.
            messagebox.showwarning(title=self.title, message=f'No backed up saves exist for {self.game.name}.')
            self.backup_restore_in_progress = False
            return


        def close_restore_win():
            '''
            Notifies the program that the restore process is complete and closes the restore window.
            '''
            self.backup_restore_in_progress = False
            self.Restore_Game_Window.destroy()


        def restore_selected_save():
            '''
            Restores selected game save based on save clicked within the Restore_Game_Window window.
            '''
            selected_backup = self.save_dic[save_listbox.get(save_listbox.curselection())]
            full_save_path = os.path.join(self.backup_dest, self.game.name, selected_backup.name)
            # check if the last post restore save is being restored
            if self.post_save_name in selected_backup.name:
                msg = 'This will delete the previously restored backup.'\
                      '\nAre you sure that you revert to the backup?'\
                      '\nThis will not send to the recycle bin.'
                response = messagebox.askyesno(title=self.title, message=msg)
                if response:
                    self.restore.delete_dir_contents(self.game.save_location)
                    self.restore.backup_orignal_save(selected_backup, full_save_path)
                    self.logger.info(f'Restored {self.post_save_name} for {self.game.name}.')
            else:
                # check if a last restore backup exists already
                for item in os.scandir(os.path.join(self.backup_dest, self.game.name)):
                    if self.post_save_name in item.name:
                        msg = f'Backup of Post-Restore Save already exists.'\
                              '\nDo you want to delete it in order to continue?'
                        response = messagebox.askyesno(title=self.title, message=msg)
                        if response:
                            # finds the post_save_name
                            for f in os.scandir(os.path.join(self.backup_dest, self.game.name)):
                                if self.post_save_name in f.name:
                                    # deletes the compressed file or deletes the entire folder tree
                                    if self.backup.compressed(f.name):
                                        os.remove(f)
                                    else:
                                        shutil.rmtree(f)
                            self.logger.info(f'Deleted original save before last restore for {self.game.name}.')
                        else:
                            print('Canceling Restore.')
                            self.Restore_Game_Window.grab_release()
                            return
                dest = os.path.join(self.backup_dest, self.game.name, self.post_save_name)
                self.backup.compress(self.game.save_location, dest)
                self.restore.delete_dir_contents(self.game.save_location)  # delete existing save
                self.restore.backup_orignal_save(selected_backup, full_save_path)
            close_restore_win()


        self.Restore_Game_Window = Tk.Toplevel(takefocus=True)
        self.Restore_Game_Window.protocol("WM_DELETE_WINDOW", close_restore_win)
        window_width = 300
        window_height = 220
        self.tk_window_options(self.Restore_Game_Window, window_width, window_height)
        self.Restore_Game_Window.grab_set()

        RestoreInfo = ttk.Label(self.Restore_Game_Window,
            text='Select save to restore for', font=("Arial Bold", 10))
        RestoreInfo.grid(columnspan=2, row=0, column=0, pady=(10,0), padx=10)

        RestoreGame = ttk.Label(self.Restore_Game_Window,
            text=self.game.name, font=("Arial Bold", 10))
        RestoreGame.grid(columnspan=2, row=1, column=0, pady=(0,10), padx=10)

        save_listbox = Tk.Listbox(self.Restore_Game_Window, exportselection=False, font=("Arial Bold", 12), height=5,
            width=30)
        save_listbox.grid(columnspan=2, row=2, column=0, pady=5, padx=10)

        for item in self.save_dic:
            save_listbox.insert(Tk.END, item)

        confirm_button = ttk.Button(self.Restore_Game_Window, text='Confirm', command=restore_selected_save, width=20)
        confirm_button.grid(row=3, column=0, padx=10, pady=10)

        CancelButton = ttk.Button(self.Restore_Game_Window, text='Cancel', command=close_restore_win, width=20)
        CancelButton.grid(row=3, column=1, padx=10, pady=10)

        self.Restore_Game_Window.mainloop()


    def explore_folder(self, folder):
        '''
        Opens the selected games save location in explorer or backup folder.

        Arguments:

        folder -- Set to "Game Save" or "Backup" to determine folder that is opened in explorer
        '''
        if self.game.name == None:
            messagebox.showwarning(title=self.title, message='No game is selected.')
        elif folder == 'Game Save':  # open game save location in explorer
            if not os.path.isdir(self.game.save_location):
                msg = f'Save location for {self.game.name} no longer exists'
                messagebox.showwarning(title=self.title, message=msg)
            subprocess.Popen(f'explorer "{self.game.save_location}"')
        elif folder == 'Backup':  # open game backup location in explorer
            if not os.path.isdir(self.game.backup_loc):
                messagebox.showwarning(title=self.title, message=f'{self.game.name} has not been backed up yet.')
            subprocess.Popen(f'explorer "{self.game.backup_loc}"')


    def add_game_to_database(self):
        '''
        Adds game to database using entry inputs.
        '''
        game_name = self.GameNameEntry.get()
        save_location = self.GameSaveEntry.get().replace('/', '\\')
        if len(self.game.get_filename(game_name)) == 0:
            messagebox.showwarning(title=self.title,message=f'Game name has no legal characters for a filename')
            return
        if self.game.exists_in_db(game_name):
            msg = f"Can't add {self.game.name} to database.\nGame already exists."
            messagebox.showwarning(title=self.title, message=msg)
        else:
            if os.path.isdir(save_location):
                self.game.add(game_name, save_location)
                # delete entry data
                self.GameSaveEntry.delete(0, Tk.END)
                self.GameNameEntry.delete(0, Tk.END)
                # update listbox with new game
                self.sorted_list.insert(0, game_name)
                self.game_listbox.insert(0, game_name)
                self.update_listbox()
                self.logger.info(f'Added {game_name} to database.')
            else:
                msg = f'Save Location for {game_name} does not exist.'
                messagebox.showwarning(title=self.title, message=msg)


    def open_smart_browse_window(self):
        '''
        Smart Browse Progress window
        '''
        # closes window if it is already open so a new one can be created
        # TODO switch to method without try block
        try:
            self.smart_browse_win.destroy()
        except AttributeError:
            pass
        # opens window
        self.smart_browse_win = Tk.Toplevel(self.main_gui)
        self.smart_browse_win.attributes('-topmost', 'true')
        self.tk_window_options(self.smart_browse_win, 340, 130, define_size=0)

        text = f'Looking for the game save directory for\n{self.GameNameEntry.get()}'
        self.info_label = Tk.Label(self.smart_browse_win, text=text, font=("Arial Bold", 10))
        self.info_label.grid(row=0, column=0, pady=(9))

        self.progress = ttk.Progressbar(self.smart_browse_win, orient=Tk.HORIZONTAL, length=360, mode='determinate')
        self.progress.grid(row=1, column=0, pady=(5,10), padx=20)

        self.s_browse = ttk.Button(self.smart_browse_win, text='Browse', command=lambda: self.browse(self.best_dir),
            width=23)
        self.s_browse.grid(row=2, column=0, pady=(5,10))
        self.s_browse.config(state='disabled')
        self.smart_browse_win.focus_force()


    @staticmethod
    def nonascii(string):
        '''
        Returns the given string with ASCII characters removed.
        '''
        return string.encode("ascii", "ignore").decode()


    @staticmethod
    def completion_sound():
        '''
        Makes a sound denoting a task completion.
        '''
        if sys.platform == 'win32':
            winsound.PlaySound("Exclamation", winsound.SND_ALIAS)


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
        initialdir = "C:/"
        self.best_dir = initialdir
        if self.debug:
            print(f'\nGame: {self.game.filename}')
        # waits for search directories to be ready before the save search is started
        while not self.save_search.directories_ready:
            print('waiting')
            sleep(.1)
        # disables progress bar actions when testing
        if test == 0:
            self.progress['maximum'] = len(self.save_search.directories) + 1
        for directory in self.save_search.directories:
            if self.debug:
                print(f'\nCurrent Search Directory: {directory}')
            directory_start = perf_counter()
            # TODO make its own function
            for root, dirs, files in os.walk(directory, topdown=False):
                for dir in dirs:
                    # TODO check if search can be ended sooner
                    if self.game.get_filename(full_game_name).lower().replace(' ', '') in dir.lower().replace(' ', ''):
                        possible_dir = os.path.join(root, dir)
                        current_score = self.save_search.dir_scoring(possible_dir)
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
        if self.best_dir == initialdir:
            app_id = self.save_search.get_appid(full_game_name)
            if app_id != None:
                app_id_path = self.save_search.check_userdata(app_id)
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
        if self.best_dir != initialdir:
            if dir_changed:
                # adds info that the found save location is not the same as the save location in the entry box
                info += f'\nFound directory is different then entered directory.'
            self.s_browse.config(state='normal')


    def smart_browse(self):
        '''
        Searches for a starting point for the save location browser.
        '''
        # checks if no game name is in entry box.
        game_name = self.GameNameEntry.get()
        if game_name == None:
            messagebox.showwarning(
                title=self.title,
                message='Smart Browse requires a game name to be entered.')
            return
        self.open_smart_browse_window()
        # looks for folders with the games name
        Thread(target=self.game_save_location_search, args=(game_name,), daemon=True).start()


    def browse(self, initial_dir=None):
        '''
        Opens a file dialog so a save directory can be chosen.
        It starts in the My Games folder in My Documents if it exists within a limited drive letter search.
        '''
        if initial_dir == None:
            starting_point = "C:/"
            current_save_location = self.GameSaveEntry.get()
            if os.path.exists(current_save_location):
                starting_point = current_save_location
        else:
            starting_point = initial_dir
            self.smart_browse_win.destroy()
        save_dir = filedialog.askdirectory(initialdir=starting_point, title="Select Save Directory")
        self.GameSaveEntry.delete(0, Tk.END)
        self.GameSaveEntry.insert(0, save_dir)


    def delete_game(self):
        '''
        Deletes selected game from SQLite Database.
        '''
        if self.game.name == None:
            messagebox.showwarning(title=self.title, message='No game is selected.')
            return
        delete_check = messagebox.askyesno(
            title=self.title,
            message=f'Are you sure that you want to delete {self.game.name}?')
        if delete_check:
            self.game.delete_from_db()
            # deletes game from game_listbox and sorted_list
            index = self.game_listbox.get(0, Tk.END).index(self.game.name)
            self.game_listbox.delete(index)
            self.sorted_list.pop(index)
            self.update_listbox()
            # checks if you want to delete the games save backups as well
            if os.path.isdir(self.game.backup_loc):
                response = messagebox.askyesno(
                    title=self.title,
                    message='Do you want to delete the backed up saves as well?')
                if response:
                    try:
                        shutil.rmtree(self.game.backup_loc)
                        self.logger.info(f'Deleted backups for{self.game.name}.')
                    except PermissionError:
                        self.logger.warning(f'Failed to delete backups for {self.game.name}')
                        messagebox.showerror(title=self.title, message='Failed to delete directory\nPermission Error')
                self.logger.info(f'Deleted {self.game.name} from database.')


    def update_game(self):
        '''
        Allows updating data for games in database.
        The last selected game in the Listbox gets updated with the info from the Add/Update Game entries.
        '''
        if self.game.name == None:
            messagebox.showwarning(title=self.title, message='No game is selected yet.')
            return
        # gets entered game info
        game_name = self.GameNameEntry.get()
        save_location = self.GameSaveEntry.get().replace('/', '\\')
        if os.path.isdir(save_location):
            old_save = self.game.save_location
            old_name = self.game.name
            old_backup = self.game.backup_loc
            self.game.update(self.game.name, game_name, save_location)
            # error when path is changed
            print(old_backup)
            print(self.game.backup_loc)
            os.rename(old_backup, self.game.backup_loc)
            # updates listbox entry for game
            if len(self.game_listbox.curselection()) != 0:
                index = self.game_listbox.curselection()
            else:
                index = 0
            self.game_listbox.delete(Tk.ACTIVE)
            self.game_listbox.insert(index, game_name)
            self.logger.info(f'Updated {self.game.name} in database.')
        else:
            messagebox.showwarning(title=self.title, message='Save Location does not exist.')


    @staticmethod
    def readable_time_since(datetime_obj):
        '''
        Gives time since for a datetime object in the unit of time that makes the most sense
        rounded to 1 decimal place.

        Arguments:

        datetime_obj -- datetime object that will have the current date subtracted from it
        '''
        seconds = (dt.datetime.now() - datetime_obj).total_seconds()
        if seconds < (60 * 60):  # seconds in minute * minutes in hour
            minutes = round(seconds / 60, 1)  # seconds in a minute
            return f' {minutes} minutes ago'
        elif seconds < (60 * 60 * 24):  # seconds in minute * minutes in hour * hours in a day
            hours = round(seconds / (60 * 60), 1)  # seconds in minute * minutes in hour
            return f' {hours} hours ago'
        else:
            days = round(seconds / 86400, 1)  # seconds in minute * minutes in hour * hours in a day
            return f' {days} days ago'


    def toggle_buttons(self, action=''):
        '''
        Disables all buttons within the buttons list.
        '''
        if action == 'disable':
            buttons = [self.ExploreBackupButton, self.ExploreSaveButton, self.BackupButton, self.RestoreButton]
            for button in buttons:
                button.config(state='disabled')
        else:
            # enables buttons that should be enabled if a game is selected
            for button in [self.BackupButton, self.ExploreSaveButton]:
                button.config(state='normal')
            # emables buttons that should be enabled if the selected game has a backup folder otherwise disables
            if os.path.isdir(self.game.backup_loc):
                set_state = 'normal'
            else:
                set_state = 'disabled'
            for button in [self.ExploreBackupButton, self.RestoreButton]:
                button.config(state=set_state)


    def update_listbox(self, data=None):
        '''
        Deletes current listbox items and adds the given data in.
        '''
        if data == None:
            # refreshes the value of sorted_list
            data = self.sorted_list
        self.game_listbox.delete(0, Tk.END)
        for item in data:
            self.game_listbox.insert(Tk.END, item)
        self.ActionInfo.config(text='Select a Game\nto continue')
        # updates title info label
        info_text = f'Total Games: {len(self.sorted_list)}\n'\
            f'Total Backup Size: {self.game.convert_size(self.backup_dest)}'
        self.Title.config(text=info_text)
        self.toggle_buttons('disable')


    def entry_search(self, e):
        '''
        Finds all items in the sorted_list that have the search box data in it.
        It then updates the listbox data to only include matching results.
        '''
        # TODO Test to be sure threading here does not cause issues.
        def search():
            typed = self.search_entry.get()
            if typed == '':
                data = self.sorted_list
            else:
                data = []
                for item in self.sorted_list:
                    if typed.lower() in item.lower():
                        data.append(item)
            self.update_listbox(data)
        Thread(target=search, daemon=True).start()


    def select_entry(self, e):
        '''
        Deletes only search box default text on click.
        '''
        if self.search_entry.get() == self.default_entry_value:
            self.search_entry.delete(0, Tk.END)


    def listbox_nav(self, e):
        '''
        Allows Up and Down arrow keys to navigate the listbox.
        '''
        index = self.game_listbox.curselection()[0]
        if e.keysym == 'Up':
            index += -1
        if e.keysym == 'Down':
            index += 1
        if 0 <= index < self.game_listbox.size():
            self.game_listbox.selection_clear(0, Tk.END)
            self.game_listbox.select_set(index)
            self.game_listbox.selection_anchor(index)
            self.game_listbox.activate(index)


    def unfocus_entry(self, e):
        '''
        Resets search box to default_entry_value when it loses focus.
        '''
        self.search_entry.delete(0, Tk.END)
        self.search_entry.insert(0, self.default_entry_value)


    def select_listbox_entry(self, Update = 0):
        '''
        Updates Game Data into Name and Save Entry for viewing.
        Allows for updating specific entries in the database as well.

        Arguments:

        Update -- 1 or 0 (default = 0)
        '''
        self.game.set(self.game_listbox.get(self.game_listbox.curselection()))
        # ignores function if listbox is empty
        if self.game_listbox.size() == 0:
            return
        # clears entry boxes
        self.GameNameEntry.delete(0, Tk.END)
        self.GameSaveEntry.delete(0, Tk.END)
        if self.backup_restore_in_progress:
            return
        # updates entry boxes to show currently selected game in listbox
        if Update == 1:
            # game name and entry box update
            self.GameNameEntry.insert(0, self.game.name)
            self.GameSaveEntry.insert(0, self.game.save_location)
            # search box update
            self.search_entry.delete(0, Tk.END)
            self.search_entry.insert(0, self.default_entry_value)
            # enables all buttons to be pressed once a selection is made
            self.toggle_buttons()
            total_size = self.game.convert_size(self.game.backup_loc)
            if self.game.last_backup == 'Never':
                info = f'{self.game.name} has not been backed up\n'
            else:
                time_since = self.readable_time_since(dt.datetime.strptime(self.game.last_backup, '%Y/%m/%d %H:%M:%S'))
                info = f'{self.game.name} was last backed up {time_since}\n'\
                    f'Game Backup Size: {total_size} from {len(os.listdir(self.game.backup_loc))} backups'
            self.ActionInfo.config(text=info)
            self.BackupButton.focus_set()


    def exit_program(self):
        '''
        Closes the database and quits the program when closing the interface.
        '''
        if self.backup_restore_in_progress:
            msg = f'Backup/Restore in progress.\n{self.title} will close after completion when you close this message.'
            messagebox.showerror(title=self.title, message=msg)
        while self.backup_restore_in_progress:
            sleep(.1)
        # BUG fails to exit if filedialog is left open
        # fix using subclassed filedialog commands that can close it
        exit()


    def open_interface_window(self):
        '''
        Opens the main Game Save Manager interface.
        '''
        start = perf_counter()
        # Defaults
        BoldBaseFont = "Arial Bold"

        self.main_gui = Tk.Tk()
        self.main_gui.protocol("WM_DELETE_WINDOW", self.exit_program)
        window_width = 680
        window_height = 550
        self.tk_window_options(self.main_gui, window_width, window_height)
        # self.main_gui.geometry(f'{window_width}x{window_height}+{width}+{height}')

        # binding
        if self.enter_to_quick_backup:
            self.main_gui.bind('<Return>', self.backup_shortcut)

        # Main Row 0
        Backup_Frame = Tk.Frame(self.main_gui)
        Backup_Frame.grid(columnspan=4, column=0, row=0,  padx=(20, 20), pady=(5, 0))

        self.Title = Tk.Label(Backup_Frame, text='\n', font=(BoldBaseFont, 10))
        self.Title.grid(columnspan=4, row=0, column=1)

        button_width = 23
        self.BackupButton = ttk.Button(Backup_Frame, text='Backup Save', state='disabled',
            command=self.run_full_backup, width=button_width)
        self.BackupButton.grid(row=3, column=1, padx=5, pady=5)

        self.RestoreButton = ttk.Button(Backup_Frame, text='Restore Save', state='disabled',
            command=self.restore_save, width=button_width)
        self.RestoreButton.grid(row=3, column=2, padx=5)

        self.ExploreSaveButton = ttk.Button(Backup_Frame, text='Explore Save Location', state='disabled',
            command=lambda: self.explore_folder('Game Save'), width=button_width)
        self.ExploreSaveButton.grid(row=4, column=1, padx=5)

        self.ExploreBackupButton = ttk.Button(Backup_Frame, text='Explore Backup Location', state='disabled',
            command=lambda: self.explore_folder('Backup'), width=button_width)
        self.ExploreBackupButton.grid(row=4, column=2, padx=5)

        # Main Row 1
        instruction = 'Select a Game\nto continue'
        self.ActionInfo = Tk.Label(self.main_gui, text=instruction, font=(BoldBaseFont, 10))
        self.ActionInfo.grid(columnspan=4, row=1, column=0, padx=5, pady= 5)

        # Main Row 2
        self.ListboxFrame = Tk.Frame(self.main_gui)
        self.ListboxFrame.grid(columnspan=4, row=2, column=0,  padx=(20, 20), pady=(5, 10))

        self.scrollbar = Tk.Scrollbar(self.ListboxFrame, orient=Tk.VERTICAL)
        self.scrollbar.grid(row=1, column=3, sticky='ns', rowspan=3)

        self.search_entry = Tk.ttk.Entry(self.ListboxFrame, width=89, exportselection=0)
        self.search_entry.grid(columnspan=3, row=0, column=0, pady=(0, 3))
        self.search_entry.insert(0, self.default_entry_value)
        self.search_entry.bind('<1>', self.select_entry)
        self.search_entry.bind('<FocusOut>', self.unfocus_entry)
        self.search_entry.bind('<KeyRelease>', self.entry_search)

        self.game_listbox = Tk.Listbox(self.ListboxFrame, exportselection=False, yscrollcommand=self.scrollbar.set,
            font=(BoldBaseFont, 12), height=10, width=60)
        self.game_listbox.grid(columnspan=3, row=1, column=0)
        self.game_listbox.bind('<<ListboxSelect>>', lambda event,
            game_listbox=self.game_listbox,:self.select_listbox_entry(1))

        # TODO finish or delete up and down control of listbox
        # full interface bind for lisxtbox navigation
        # self.main_gui.bind('<Up>', lambda event,arg=.1:self.listbox_nav(event))
        # self.main_gui.bind('<Down>', lambda event,arg=.1:self.listbox_nav(event))

        # scrollbar config
        self.scrollbar.config(command=self.game_listbox.yview)
        # listbox fill
        self.sorted_list = self.game.sorted_games()
        self.update_listbox()

        # Main Row 3
        Add_Game_Frame = Tk.LabelFrame(self.main_gui, text='Manage Games')
        Add_Game_Frame.grid(columnspan=4, row=3, padx=15, pady=(5, 17))

        EnterGameLabel = Tk.ttk.Label(Add_Game_Frame, text='Enter Game Name')
        EnterGameLabel.grid(row=0, column=0)

        entry_width = 65
        self.GameNameEntry = Tk.ttk.Entry(Add_Game_Frame, width=entry_width, exportselection=0)
        self.GameNameEntry.grid(row=0, column=1, columnspan=3, pady=8, padx=5)

        EnterSaveLabeL = Tk.ttk.Label(Add_Game_Frame, text='Enter Save Location')
        EnterSaveLabeL.grid(row=1, column=0)

        self.GameSaveEntry = Tk.ttk.Entry(Add_Game_Frame, width=entry_width, exportselection=0)
        self.GameSaveEntry.grid(row=1, column=1, columnspan=3, pady=5, padx=10)

        browse_button_width = 13
        SmartBrowseButton = Tk.ttk.Button(Add_Game_Frame, text='Smart Browse', width=browse_button_width,
            command=self.smart_browse)
        SmartBrowseButton.grid(row=0, column=4, padx=10)

        BrowseButton = Tk.ttk.Button(Add_Game_Frame, text='Browse', width=browse_button_width,
            command=self.browse)
        BrowseButton.grid(row=1, column=4, padx=10)

        # Button Frame Row 2
        Button_Frame = Tk.Frame(Add_Game_Frame)
        Button_Frame.grid(columnspan=5, row=2, pady=(5, 5))

        button_padx = 4
        button_pady = 5
        ConfirmAddButton = Tk.ttk.Button(Button_Frame, text='Add Game',
            command=self.add_game_to_database, width=16)
        ConfirmAddButton.grid(row=2, column=0, padx=button_padx, pady=button_pady)

        UpdateButton = Tk.ttk.Button(Button_Frame, text='Update Game',
            command=self.update_game, width=16)
        UpdateButton.grid(row=2, column=1, padx=button_padx, pady=button_pady)

        RemoveButton = ttk.Button(Button_Frame, text='Remove Game',
            command=self.delete_game, width=16)
        RemoveButton.grid(row=2, column=2, padx=button_padx, pady=button_pady)

        ClearButton = Tk.ttk.Button(Button_Frame, text='Clear Entries',
            command=self.select_listbox_entry, width=16)
        ClearButton.grid(row=2, column=3, padx=button_padx, pady=button_pady)

        ClearButton = Tk.ttk.Button(Button_Frame, text='Refresh Games', command=self.update_listbox, width=16)
        ClearButton.grid(row=2, column=4, padx=button_padx, pady=button_pady)

        self.game.database_check()

        # interface startup time check
        end = perf_counter()
        start_elapsed = round(end-start, 2)
        if start_elapsed > 1:
            print('Interface Ready: ', start_elapsed)
        self.main_gui.mainloop()


    def run(self):
        '''
        Runs everything needed to make the program work.
        '''
        if self.output:
            sys.stdout = open("output.txt", "w")
        self.backup_dest_check()
        # opens the interface
        self.open_interface_window()
        if self.output:
            sys.stdout.close()


if __name__ == '__main__':
    GUI().run()
