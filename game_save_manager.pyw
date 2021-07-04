import getpass, sqlite3, shutil, json, os, re, sys, subprocess, math
from time import sleep, perf_counter
from threading import Thread
from tkinter import ttk, filedialog, messagebox
import tkinter as Tk
import datetime as dt
from game import game_class
# optional imports
try:
    import winsound
    winsound_installed = 1
except ModuleNotFoundError:
    winsound_installed = 0

class Gui:

    # sets script directory in case current working directory is different
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # var init
    title = 'Game Save Manager'
    default_entry_value = 'Type Search Query Here'

    game = game_class()


    def startup_check(self):
        '''
        ph
        '''
        # checks for missing saves
        missing_save_list= self.game.database_check()
        total = len(missing_save_list)
        if total > 0:
            if total == 1:
                plural = ''
            else:
                plural = 's'
            msg = f'{total} save location{plural} currently no longer exists.\n'\
                  f'Do you want to show only the missing game{plural}?\n'\
                   'Click Refresh Games to show all entries again.'
            response = messagebox.askyesno(title=self.title, message=msg)
            if response:
                self.update_listbox(missing_save_list)
        # Checks if backup destination in settings exists and asks if you want to choose one if it does not.
        Tk.Tk().withdraw()
        if not os.path.exists(self.game.backup_dest):
            msg = 'Do you want to choose a save backup directory instead of using a default within the program folder?'
            response = messagebox.askyesno(title=self.title, message=msg)
            if response:
                self.game.backup_dest = filedialog.askdirectory(initialdir="C:/", title="Select Save Backup Directory")
                if os.path.exists(self.game.backup_dest):
                    self.data['settings']['backup_dest'] = self.game.backup_dest
                    json_object = json.dumps(self.data, indent = 4)  # Serializing json
                    with open('settings.json', "w") as outfile:  # Writing to sample.json
                        outfile.write(json_object)
                else:
                    messagebox.showwarning(title=self.title, message='Path does not exist.')
            else:
                os.mkdir(self.game.backup_dest)


    def backup_button(self):
        '''
        Backups up the game entered based on SQLite save location data to the specified backup folder.
        '''
        info1 = f'{self.game.name} has been backed up.\n'
        # BUG total_size is wrong for some games right after it finishes backing up
        info2 = f'Game Backup Size: {self.game.backup_size} from {len(os.listdir(self.game.backup_loc))} backups'
        if self.game.enable_debug:
            print(info2)
        self.ActionInfo.config(text=info1 + info2)
        self.game_listbox.delete(Tk.ACTIVE)
        self.game_listbox.insert(0, self.game.name)
        self.game.logger.info(f'Backed up Save for {self.game.name}.')
        if self.game.name == None:
            messagebox.showwarning(title=self.title, message='No game is selected yet.')
            return
        game_name = self.game.name
        self.ActionInfo.config(text=f'Backing up {game_name}\nDo not close program.')
        try:
            Thread(target=self.game.backup, args=(game_name,)).start()
            self.game.logger.info(f'{self.game.name} had more then {self.game.backup_redundancy} Saves. Deleted oldest saves.')
        except FileNotFoundError:
            messagebox.showwarning(title=self.title,  message='Action Failed - File location does not exist.')
            self.game.logger.error(f'Failed to Backed up Save for {game_name}. File location does not exist.')
        except FileExistsError:
            messagebox.showwarning(title=self.title, message='Action Failed - Save Already Backed up.')
            self.game.logger.error(f'Failed to Backed up Save for {game_name}. Save Already Backed up.')
        except SystemExit:
            print('Cancelled Backup.')


    def restore_button(self):
        '''
        ph
        '''
        pass


    def update_button(self):
        '''
        Allows updating data for games in database.
        The last selected game in the Listbox gets updated with the info from the Add/Update Game entries.
        '''
        new_name = self.GameNameEntry.get()
        new_save = self.GameSaveEntry.get().replace('/', '\\')
        if self.game.name == None:
            messagebox.showwarning(title=self.title, message='No game is selected yet.')
            return
        # gets entered game info
        game_name = self.GameNameEntry.get()
        save_location = self.GameSaveEntry.get().replace('/', '\\')
        if os.path.isdir(save_location):
            # updates data in database
            sql_update_query  ='''UPDATE games
                    SET game_name = ?, save_location = ?
                    WHERE game_name = ?;'''
            data = (game_name, save_location, self.game.name)
            self.game.cursor.execute(sql_update_query , data)
            self.game.database.commit()
            new_name = os.path.join(self.game.backup_dest, self.get_selected_game_filename(game_name))
            os.rename(self.game.backup_dest, new_name)
            self.game.backup_dest = new_name
            # updates listbox entry for game
            if len(self.game_listbox.curselection()) != 0:
                index = self.game_listbox.curselection()
            else:
                index = 0
            self.game_listbox.delete(Tk.ACTIVE)
            self.game_listbox.insert(index, game_name)
            self.game.logger.info(f'Updated {self.game.name} in database.')
        else:
            messagebox.showwarning(title=self.title, message='Save Location does not exist.')


    def add_game(self):
        game_name = self.GameNameEntry.get()
        save_location = self.GameSaveEntry.get().replace('/', '\\')
        if len(self.get_selected_game_filename(game_name)) == 0:
            messagebox.showwarning(title=self.title,message=f'Game name has no legal characters for a filename')
            return
        if self.game.save_location != None:
            msg = f"Can't add {self.game.name} to database.\nGame already exists."
            messagebox.showwarning(title=self.title, message=msg)
        else:
            if os.path.isdir(save_location):
                self.GameSaveEntry.delete(0, Tk.END)
                self.GameNameEntry.delete(0, Tk.END)
                self.cursor.execute("INSERT INTO games VALUES (:game_name, :save_location, :last_backup)",
                    {'game_name': game_name, 'save_location': save_location, 'last_backup': 'Never'})
                self.database.commit()
                self.sorted_list.insert(0, game_name)
                self.game_listbox.insert(0, game_name)
                self.game.logger.info(f'Added {game_name} to database.')
                self.update_listbox()
            else:
                msg = f'Save Location for {self.game.name} does not exist.'
                messagebox.showwarning(title=self.title, message=msg)


    def tk_window_options(self, window_name, window_width, window_height, define_size=0):
        '''
        Disables window resize and centers window if config enables each.
        '''
        window_name.title(self.title)
        if sys.platform == 'win32':
            window_name.iconbitmap(window_name, 'images\Save_icon.ico')
        if self.game.disable_resize:  # sets window to not resize if disable_resize is set to 1
            window_name.resizable(width=False, height=False)
        if self.game.center_window == 1:
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
            # TODO move some variables to here as arguments to make sure everything stays the same
            self.game.backup_button()
        else:
            self.game_listbox.activate(0)
            return
        print(event)


    def restore_save(self):
        '''
        Opens an interface for picking the dated backup of the selected game to restore.

        First it checks if an existing save exists or if a game is even selected(Exits function if no game is selected).
        '''
        # exits if no game is selected
        if self.game.name == None:
            messagebox.showwarning(title=self.title, message='No game is selected yet.')
            return
        self.game.backup_restore_in_progress = 1  # disables closing the interface until restore completes
        # checks if the game has a backup folder
        if os.path.exists(self.game.backup_dest):
            # creates list of backups that can be restored
            self.save_dic = {}
            for file in os.scandir(self.game.backup_dest):
                file_name = os.path.splitext(file.name)[0]
                if file_name == 'Post-Restore Save':
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
            self.game.backup_restore_in_progress = 0
            return


        def close_restore_win():
            '''
            Notifies the program that the restore process is complete and closes the restore window.
            '''
            self.game.backup_restore_in_progress = 0
            self.Restore_Game_Window.destroy()


        def delete_dir_contents(dir):
            '''
            Deletes all files and folders within the given directory.
            '''
            for f in os.scandir(dir):
                if os.path.isdir(f):
                    shutil.rmtree(f)
                else:
                    os.remove(f)


        def restore_selected_save():
            '''
            Restores selected game save based on save clicked within the Restore_Game_Window window.
            '''
            selected_backup = self.save_dic[save_listbox.get(save_listbox.curselection())]
            full_save_path = os.path.join(self.game.backup_dest, self.game.name, selected_backup.name)
            post_save_name = 'Post-Restore Save'
            # check if the last post restore save is being restored
            if post_save_name in selected_backup.name:
                msg = 'This will delete the previously restored backup.'\
                      '\nAre you sure that you revert to the backup?'\
                      '\nThis will not send to the recycle bin.'
                response = messagebox.askyesno(title=self.title, message=msg)
                if response:
                    delete_dir_contents(self.game.save_location)
                    log_msg = self.backup_orignal_save(selected_backup, full_save_path)
                    self.game.logger.info(log_msg)
                    self.game.logger.info(f'Restored {post_save_name} for {self.game.name}.')
            else:
                # check if a last restore backup exists already
                for item in os.scandir(os.path.join(self.game.backup_dest, self.game.name)):
                    if post_save_name in item.name:
                        msg = f'Backup of Post-Restore Save already exists.'\
                              '\nDo you want to delete it in order to continue?'
                        response = messagebox.askyesno(title=self.title, message=msg)
                        if response:
                            # finds the post_save_name
                            for f in os.scandir(os.path.join(self.game.backup_dest, self.game.name)):
                                if post_save_name in f.name:
                                    # deletes the compressed file or deletes the entire folder tree
                                    if self.compressed(f.name):
                                        os.remove(f)
                                    else:
                                        shutil.rmtree(f)
                            self.game.logger.info(f'Deleted original save before last restore for {self.game.name}.')
                        else:
                            print('Canceling Restore.')
                            self.Restore_Game_Window.grab_release()
                            return
                dest = os.path.join(self.game.backup_dest, self.game.name, post_save_name)
                self.compress(self.game.save_location, dest)
                delete_dir_contents(self.game.save_location)  # delete existing save
                self.backup_orignal_save(selected_backup, full_save_path)
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
            messagebox.showwarning(title=self.title, message='No game is selected yet.')
        elif folder == 'Game Save':  # open game save location in explorer
            if not os.path.isdir(self.game.save_location):
                msg = f'Save location for {self.game.name} no longer exists'
                messagebox.showwarning(title=self.title, message=msg)
            subprocess.Popen(f'explorer "{self.game.save_location}"')
        elif folder == 'Backup':  # open game backup location in explorer
            if not os.path.isdir(self.game.backup_dest):
                messagebox.showwarning(title=self.title, message=f'{self.game.name} has not been backed up yet.')
            subprocess.Popen(f'explorer "{self.game.backup_dest}"')


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
        if self.game.enable_debug:
            print(result)
        return result


    def open_smart_browse_window(self):
        '''
        Smart Browse Progress window
        TODO create index of each directory and use changes in directory to see if a new index should be done.
        '''
        # closes window if it is already open so a new one can be created
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
            if winsound_installed:
                winsound.PlaySound("Exclamation", winsound.SND_ALIAS)


    def smart_browse(self):
        '''
        Searches for a starting point for the save location browser.
        '''
        # removes illegal file characters
        full_game_name = self.GameNameEntry.get()
        # checks if no game name is in entry box.
        if len(full_game_name) == 0:
            messagebox.showwarning(
                title=self.title,
                message='Smart Browse requires a game name to be entered.')
            return
        self.open_smart_browse_window()
        # looks for folders with the games name
        Thread(target=self.game_save_location_search, args=(full_game_name,), daemon=True).start()


    def browse(self, initial_dir=None):
        '''
        Opens a file dialog so a save directory can be chosen.
        It starts in the My Games folder in My Documents if it exists within a limited drive letter search.
        '''
        if initial_dir == None:
            starting_point = self.initialdir
            current_save_location = self.GameSaveEntry.get()
            if os.path.exists(current_save_location):
                starting_point = current_save_location
        else:
            starting_point = initial_dir
            self.smart_browse_win.destroy()
        save_dir = filedialog.askdirectory(initialdir=starting_point, title="Select Save Directory")
        self.GameSaveEntry.delete(0, Tk.END)
        self.GameSaveEntry.insert(0, save_dir)


    def delete_game_from_db(self):
        '''
        Deletes selected game from SQLite Database.
        '''
        if self.game.name == None:
            messagebox.showwarning(title=self.title, message='No game is selected yet.')
            return
        delete_check = messagebox.askyesno(
            title=self.title,
            message=f'Are you sure that you want to delete {self.game.name}?')
        if delete_check:
            self.game.delete()
            # deletes game from game_listbox and sorted_list
            self.game_listbox.delete(self.game.name)
            self.sorted_list.pop(self.game.name)
            self.update_listbox()
            self.select_listbox_entry()
            # checks if you want to delete the games save backups as well
            if os.path.isdir(self.game.backup_dest):
                response = messagebox.askyesno(
                    title=self.title,
                    message='Do you want to delete the backed up saves as well?')
                if response:
                    if not self.game.delete_saves():
                        messagebox.showerror(title=self.title, message='Failed to delete directory\nPermission Error')
            self.game.logger.info(f'Deleted {self.game.name} from database.')


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
        info_text = f'Total Games: {len(self.sorted_list)}\nTotal Backup Size: {self.game.convert_size(self.game.backup_dest)}'
        self.Title.config(text=info_text)


    def entry_search(self, e):
        '''
        Finds all items in the sorted_list that have the search box data in it.
        It then updates the listbox data to only include matching results.
        '''
        typed = self.search_entry.get()
        if typed == '':
            data = self.sorted_list
        else:
            data = []
            for item in self.sorted_list:
                if typed.lower() in item.lower():
                    data.append(item)
        self.update_listbox(data)


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
        # ignores function if listbox is empty
        if self.game_listbox.size() == 0:
            return
        # clears entry boxes
        self.GameNameEntry.delete(0, Tk.END)
        self.GameSaveEntry.delete(0, Tk.END)
        if self.game.backup_restore_in_progress:
            return
        # updates entry boxes to show currently selected game in listbox
        if Update == 1:
            selected_game = self.game_listbox.get(self.game_listbox.curselection())
            self.game.set(selected_game)
            # game name and entry box update
            self.GameNameEntry.insert(0, self.game.name)
            self.GameSaveEntry.insert(0, self.game.save_location)
            # search box update
            self.search_entry.delete(0, Tk.END)
            self.search_entry.insert(0, self.default_entry_value)
            # enables all buttons to be pressed once a selection is made
            for button in [self.BackupButton, self.ExploreSaveButton]:
                button.config(state='normal')
            if os.path.isdir(self.game.backup_dest):
                set_state = 'normal'
            else:
                set_state = 'disabled'
            for button in [self.ExploreBackupButton, self.RestoreButton]:
                button.config(state=set_state)
            if self.game.last_backup != 'Never':
                time_since = self.readable_time_since(dt.datetime.strptime(self.game.last_backup, '%Y/%m/%d %H:%M:%S'))
                info1 = f'{self.game.name} was last backed up {time_since}\n'
                info2 = f'Game Backup Size: {self.game.backup_size} from {len(os.listdir(self.game.backup_dest))} backups'
                info = info1 + info2
            else:
                info = f'{self.game.name} has not been backed up\n'
            self.ActionInfo.config(text=info)
            self.BackupButton.focus_set()


    def close_db(self):
        '''
        Closes the database and quits the program when closing the interface.
        '''
        if self.game.backup_restore_in_progress:
            msg = f'Backup/Restore in progress.\n{self.title} will close after completion when you close this message.'
            messagebox.showerror(title=self.title, message=msg)
        while self.game.backup_restore_in_progress:
            sleep(.1)
        self.game.database.close
        # BUG fails to exit if filedialog is left open
        # fix using subclassed filedialog commands that can close it
        exit()


    def open_interface_window(self):
        '''
        Opens the main Game Save Manager interface.
        '''
        # Defaults
        BoldBaseFont = "Arial Bold"

        self.main_gui = Tk.Tk()
        self.main_gui.protocol("WM_DELETE_WINDOW", self.close_db)
        window_width = 680
        window_height = 550
        self.tk_window_options(self.main_gui, window_width, window_height)
        # self.main_gui.geometry(f'{window_width}x{window_height}+{width}+{height}')

        # binding
        if self.game.enter_to_quick_backup:
            self.main_gui.bind('<Return>', self.backup_shortcut)

        # Main Row 0
        Backup_Frame = Tk.Frame(self.main_gui)
        Backup_Frame.grid(columnspan=4, column=0, row=0,  padx=(20, 20), pady=(5, 0))

        self.Title = Tk.Label(Backup_Frame, text='\n', font=(BoldBaseFont, 10))
        self.Title.grid(columnspan=4, row=0, column=1)

        button_width = 23
        self.BackupButton = ttk.Button(Backup_Frame, text='Backup Save', state='disabled',
            command=self.backup_button, width=button_width)
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
        self.game_listbox.bind('<<ListboxSelect>>', lambda event, game_listbox=self.game_listbox,:self.select_listbox_entry(1))

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
            command=self.add_game, width=16)
        ConfirmAddButton.grid(row=2, column=0, padx=button_padx, pady=button_pady)

        UpdateButton = Tk.ttk.Button(Button_Frame, text='Update Game',
            command=self.update_button, width=16)
        UpdateButton.grid(row=2, column=1, padx=button_padx, pady=button_pady)

        RemoveButton = ttk.Button(Button_Frame, text='Remove Game',
            command=self.delete_game_from_db, width=16)
        RemoveButton.grid(row=2, column=2, padx=button_padx, pady=button_pady)

        ClearButton = Tk.ttk.Button(Button_Frame, text='Clear Entries',
            command=self.select_listbox_entry, width=16)
        ClearButton.grid(row=2, column=3, padx=button_padx, pady=button_pady)

        ClearButton = Tk.ttk.Button(Button_Frame, text='Refresh Games', command=self.update_listbox, width=16)
        ClearButton.grid(row=2, column=4, padx=button_padx, pady=button_pady)

        self.main_gui.mainloop()


    def run(self):
        '''
        Runs everything needed to make the program work.
        '''
        if self.game.output:
            sys.stdout = open("output.txt", "w")
        Thread(target=self.game.find_search_directories).start()
        self.startup_check()
        self.open_interface_window()
        if self.game.output:
            sys.stdout.close()


if __name__ == '__main__':
    Gui().run()
