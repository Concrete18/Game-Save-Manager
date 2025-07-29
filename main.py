# standard library
from tkinter import ttk, filedialog, messagebox
import tkinter as Tk
import shutil, os, sys, winsound, time
from threading import Thread
import datetime as dt

# sets script directory in case current working directory is different
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# local application imports
from config.config import Config
from classes.game import Game
from classes.database import Database
from classes.helper import *
from classes.backup import Backup
from classes.restore import Restore


class SaveManager:
    def __init__(self):
        # config setup
        self.cfg = Config("config/settings.ini")
        self.cfg.get_settings()

        # var init
        self.title = "Game Save Manager"
        self.allowed_filename_characters = r"[^a-zA-Z0-9.,\s]"
        self.backup_restore_in_progress = False
        self.default_entry_value = "Type Search Query Here"
        self.post_save_name = "Post-Restore Save"

        # game class
        self.database = Database(
            backup_folder=self.cfg.backup_folder, db_loc="config/game.db"
        )
        self.backup = Backup(self.database, self.cfg.compression_type)
        self.restore = Restore(self.database, self.backup)

        self.cur_game = Game()

    @benchmark
    def backup_folder_check(self):
        """
        Checks if backup destination in settings exists and asks if you want
        to choose one if it does not.
        """
        Tk.Tk().withdraw()
        if not os.path.exists(self.cfg.backup_folder):
            msg = "Do you want to choose a save backup directory instead of using a default within the program folder?"
            response = messagebox.askyesno(title=self.title, message=msg)
            if response:
                title = "Select Save Backup Directory"
                new_backup_folder = filedialog.askdirectory(
                    mustexist=True,
                    initialdir=script_dir,
                    title=title,
                )
                if os.path.exists(new_backup_folder):
                    self.cfg.backup_folder = new_backup_folder
                    self.cfg.set_setting(
                        "SETTINGS",
                        "backup_folder",
                        new_backup_folder,
                    )
                else:
                    msg = "Path does not exist."
                    messagebox.showwarning(title=self.title, message=msg)
            else:
                os.mkdir(self.cfg.backup_folder)

    def set_info_text(self, msg: str) -> None:
        """
        Sets the interface info text to `msg`.
        If sound is given as `"success"` or `"warning"`, it will play the sound
        after updating the text.
        """
        REQUIRED_NEW_LINES = 2
        missing_new_lines = REQUIRED_NEW_LINES - msg.count("\n")
        for _ in range(missing_new_lines):
            msg += "\n"
        self.ActionInfo.config(text=msg)

    def run_full_backup(self):
        """
        Backups up the game entered based on SQLite save location data to the
        specified backup folder.
        """
        if not self.cur_game:
            print("No game is set")
            return
        # sets selected game so other games can be selected during backup without issue
        selected_game = self.cur_game

        def backup():
            """
            Runs a single backup for the entered arg.
            Also sets self.backup_restore_in_progress to True so the program
            wont quick during a backup. Function is ready to be run as a thread.
            """
            self.backup_restore_in_progress = True
            current_time = dt.datetime.now().strftime("%m-%d-%y %H-%M-%S")
            self.backup.compress(
                selected_game.save_location, selected_game.backup_path, current_time
            )
            if not os.path.exists(selected_game.backup_path):
                self.warning_sound()
                return
            self.backup.delete_oldest(
                selected_game.name,
                selected_game.backup_path,
                self.cfg.backup_redundancy,
                self.post_save_name,
            )
            time.sleep(0.3)
            # BUG total_size is wrong for some games right after it finishes backing up
            total_backups = len(os.listdir(selected_game.backup_path))
            msg = f"{selected_game.name} has been backed up.\nGame Backup Size: {self.cur_game.backup_size} from {total_backups} backups\n"
            self.set_info_text(msg=msg)
            self.backup_restore_in_progress = False
            self.completion_sound()

        # nothing is selected
        if selected_game.name is None:
            msg = "No game is selected yet."
            self.set_info_text(msg=msg)
            self.warning_sound()
        # save path does not exists
        elif not os.path.exists(self.cur_game.save_location):
            msg = "Save no longer exists."
            self.set_info_text(msg=msg)
            self.warning_sound()
        # actual run if it clears
        else:
            # checks if current folder and previous backup hashes are identical
            game_current_hash = get_hash(self.cur_game.save_location)
            # gets last info text so double click backup works
            last_text = self.ActionInfo.cget("text").replace("\n", "")
            msg = f"{selected_game.name}\nSave has not changed since last backup.\nPress Enter again to force backup."
            if not selected_game.is_new_hash(game_current_hash) and last_text != msg:
                self.set_info_text(msg=msg)
                self.warning_sound()
                return
            # moves clicked game to the top
            self.game_listbox.delete(Tk.ACTIVE)
            self.game_listbox.insert(0, selected_game.name)
            self.ActionInfo.config(
                text=f"Backing up {selected_game.name}\nDo not close program.\n"
            )
            # starts backup function as a new thread
            Thread(target=backup).start()
            self.database.update_previous_backup_hash(
                selected_game.name, selected_game.curr_save_hash
            )
            self.database.update_last_backup(selected_game.name)

    def tk_window_options(
        self, window_name, window_width, window_height, define_size=0
    ):
        """
        Disables window resize and centers window if config enables each.
        """
        window_name.title(self.title)
        if sys.platform == "win32":
            window_name.iconbitmap(window_name, "images/Save_icon.ico")
        if (
            self.cfg.disable_resize
        ):  # sets window to not resize if disable_resize is set to 1
            window_name.resizable(width=False, height=False)
        if self.cfg.center_window == 1:
            width_pos = int((window_name.winfo_screenwidth() - window_width) / 2)
            height_pos = int((window_name.winfo_screenheight() - window_height) / 2)
            if define_size:
                window_name.geometry(
                    f"{window_width}x{window_height}+{width_pos}+{height_pos}"
                )
            else:
                window_name.geometry(f"+{width_pos}+{height_pos}")

    def backup_shortcut(self, event):
        """
        Shortcut that activates when pressing enter while a game is selected.
        """
        # TODO add setting so if no game is selected, it will ask if you want to backup the most recently backed up game.
        response = messagebox.askquestion(
            title=self.title,
            message=f"Are you sure you want to backup {self.cur_game.name}",
        )
        if response == "yes":
            self.run_full_backup()
        else:
            self.game_listbox.activate(0)
            return
        print(event)

    def restore_save(self):
        """
        Opens an interface for picking the dated backup of the selected game
        to restore.

        First it checks if an existing save exists or if a game is even
        selected(Exits function if no game is selected).
        """
        # TODO test Restore functions
        # exits if no game is selected
        if not self.cur_game.name:
            return
        self.backup_restore_in_progress = (
            True  # disables closing the interface until restore completes
        )
        # checks if the game has a backup folder
        if os.path.exists(self.cur_game.backup_path):
            # creates list of backups that can be restored
            self.save_dic = {}
            for file in os.scandir(self.cur_game.backup_path):
                file_name = os.path.splitext(file.name)[0]
                if file_name == self.post_save_name:
                    self.save_dic["Undo Last Restore"] = file
                    continue
                try:
                    updated_name = dt.datetime.strptime(
                        file_name, "%m-%d-%y %H-%M-%S"
                    ).strftime("%b %d, %Y %I:%M %p")
                except ValueError:
                    updated_name = file_name
                self.save_dic[updated_name] = file
        else:
            # brings up a warning if no backup exists for the selected game.
            messagebox.showwarning(
                title=self.title,
                message=f"No backed up saves exist for {self.cur_game.name}.",
            )
            self.backup_restore_in_progress = False
            return

        def close_restore_win():
            """
            Notifies the program that the restore process is complete and
            closes the restore window.
            """
            self.backup_restore_in_progress = False
            self.Restore_Game_Window.destroy()

        def restore_selected_save():
            """
            Restores selected game save based on save clicked within the
            Restore_Game_Window window.
            """
            selected_backup = self.save_dic[
                save_listbox.get(save_listbox.curselection())
            ]
            full_save_path = os.path.join(
                self.cfg.backup_folder, self.cur_game.name, selected_backup.name
            )
            # check if the last post restore save is being restored
            if self.post_save_name in selected_backup.name:
                msg = (
                    "This will delete the previously restored backup."
                    "\nAre you sure that you revert to the backup?"
                    "\nThis will not send to the recycle bin."
                )
                response = messagebox.askyesno(title=self.title, message=msg)
                if response:
                    self.restore.delete_dir_contents(self.cur_game.save_location)
                    self.restore.decompress(
                        selected_backup.path, self.cur_game.save_location
                    )
            else:
                # check if a last restore backup exists already
                for item in os.scandir(
                    os.path.join(self.cfg.backup_folder, self.cur_game.name)
                ):
                    if self.post_save_name in item.name:
                        msg = (
                            f"Backup of Post-Restore Save already exists."
                            "\nDo you want to delete it in order to continue?"
                        )
                        response = messagebox.askyesno(title=self.title, message=msg)
                        if response:
                            # finds the post_save_name
                            backup_folder = os.path.join(
                                self.cfg.backup_folder, self.cur_game.name
                            )
                            for f in os.scandir(backup_folder):
                                if self.post_save_name in f.name:
                                    os.remove(f)
                        else:
                            print("Canceling Restore.")
                            self.Restore_Game_Window.grab_release()
                            return
                dest = os.path.join(self.cfg.backup_folder, self.cur_game.name)
                self.backup.compress(
                    self.cur_game.save_location, dest, self.post_save_name
                )
                self.restore.delete_dir_contents(
                    self.cur_game.save_location
                )  # delete existing save
                self.restore.decompress(
                    selected_backup.path, self.cur_game.save_location
                )
            close_restore_win()

        self.Restore_Game_Window = Tk.Toplevel(takefocus=True)
        self.Restore_Game_Window.protocol("WM_DELETE_WINDOW", close_restore_win)
        window_width = 300
        window_height = 220
        self.tk_window_options(self.Restore_Game_Window, window_width, window_height)
        self.Restore_Game_Window.grab_set()

        RestoreInfo = ttk.Label(
            self.Restore_Game_Window,
            text="Select save to restore for",
            font=("Arial Bold", 10),
        )
        RestoreInfo.grid(columnspan=2, row=0, column=0, pady=(10, 0), padx=10)

        RestoreGame = ttk.Label(
            self.Restore_Game_Window, text=self.cur_game.name, font=("Arial Bold", 10)
        )
        RestoreGame.grid(columnspan=2, row=1, column=0, pady=(0, 10), padx=10)

        save_listbox = Tk.Listbox(
            self.Restore_Game_Window,
            exportselection=False,
            font=("Arial Bold", 12),
            height=5,
            width=30,
        )
        save_listbox.grid(columnspan=2, row=2, column=0, pady=5, padx=10)

        for item in self.save_dic:
            save_listbox.insert(Tk.END, item)

        confirm_button = ttk.Button(
            self.Restore_Game_Window,
            text="Confirm",
            command=restore_selected_save,
            width=20,
        )
        confirm_button.grid(row=3, column=0, padx=10, pady=10)

        CancelButton = ttk.Button(
            self.Restore_Game_Window, text="Cancel", command=close_restore_win, width=20
        )
        CancelButton.grid(row=3, column=1, padx=10, pady=10)

        self.Restore_Game_Window.mainloop()

    def explore_folder(self, folder_type):
        """
        Opens the selected games save location or backup folder in explorer.

        Set `folder_type` to "Game Save" or "Backup" to select what to open in explorer.
        """
        if not self.cur_game.name:
            return

        paths = {
            "Game Save": self.cur_game.save_location,
            "Backup": self.cur_game.backup_path,
        }

        path = paths.get(folder_type)
        if path and os.path.isdir(path):
            os.startfile(path)
        else:
            match folder_type:
                case "Game Save":
                    msg = f"Save location for {self.cur_game.name} no longer exists."
                case "Backup":
                    msg = f"{self.cur_game.name} has not been backed up yet."
                case _:
                    msg = f"Unknown folder type: {folder_type}"
            messagebox.showwarning(title=self.title, message=msg)

    def add_game_to_database(self):
        """
        Adds game to database using entry inputs.
        """
        game_name = self.GameNameEntry.get()
        save_location = self.GameSaveEntry.get().replace("/", "\\")
        self.cur_game = Game(name=game_name, save_location=save_location)
        if len(self.cur_game.filename) == 0:
            msg = f"Game name has no legal characters for a filename"
            messagebox.showwarning(title=self.title, message=msg)
            return
        game_dict = self.database.get_game_info(game_name)
        if game_dict.get("save_location"):
            msg = f"Can't add {game_name} to database.\nGame already exists."
            messagebox.showwarning(title=self.title, message=msg)
        else:
            if os.path.exists(save_location):
                self.database.add(game_name, save_location)
                # delete entry data
                self.GameSaveEntry.delete(0, Tk.END)
                self.GameNameEntry.delete(0, Tk.END)
                # update listbox with new game
                self.sorted_list.insert(0, game_name)
                self.game_listbox.insert(0, game_name)
                self.update_listbox()
            else:
                msg = f"Save Location for {game_name} does not exist."
                messagebox.showwarning(title=self.title, message=msg)

    @staticmethod
    def nonascii(string):
        """
        Returns `string` with ASCII characters removed.
        """
        return string.encode("ascii", "ignore").decode()

    @staticmethod
    def completion_sound():
        """
        Makes a sound denoting a task completion.
        """

        def threaded_sound():
            """
            Function defined so it can be run in a new thread.
            """
            if sys.platform == "win32":
                winsound.PlaySound("Exclamation", winsound.SND_ALIAS)

        Thread(target=threaded_sound).start()

    @staticmethod
    def warning_sound():
        """
        Makes a sound denoting a task warning.
        """

        def threaded_sound():
            """
            Function defined so it can be run in a new thread.
            """
            if sys.platform == "win32":
                winsound.PlaySound("SystemHand", winsound.SND_ALIAS)

        Thread(target=threaded_sound).start()
        print("warning sound was played")

    def browse(self, directory="C:/"):
        """
        Opens a file dialog so a save directory can be chosen.

        TODO fix below
        It starts in the My Games folder in My Documents if it exists within
        a limited drive letter search.
        """
        msg = "Select Save Directory"
        save_dir = filedialog.askdirectory(initialdir=directory, title=msg)
        if save_dir:
            self.GameSaveEntry.delete(0, Tk.END)
            self.GameSaveEntry.insert(0, save_dir)

    def delete_game(self):
        """
        Deletes selected game from SQLite Database.
        """
        if not self.cur_game.name:
            return
        msg = f"Are you sure that you want to delete {self.cur_game.name}?"
        delete_check = messagebox.askyesno(title=self.title, message=msg)
        if delete_check:
            # BUG deletes game that is selected but often removes
            # the wrong game form the list
            self.database.delete_from_db(self.cur_game.name)
            # deletes game from game_listbox and sorted_list
            index = self.game_listbox.get(0, Tk.END).index(self.cur_game.name)
            self.game_listbox.delete(index)
            self.sorted_list.pop(index)
            self.update_listbox()
            # checks if you want to delete the games save backups as well
            if os.path.isdir(self.cur_game.backup_path):
                msg = "Do you want to delete the backed up saves as well?"
                response = messagebox.askyesno(title=self.title, message=msg)
                if response:
                    try:
                        # BUG gets permission errors often
                        shutil.rmtree(self.cur_game.backup_path)
                    except PermissionError:
                        msg = "Failed to delete directory\nPermission Error"
                        messagebox.showerror(title=self.title, message=msg)

    def update_game(self):
        """
        Allows updating data for games in database.
        The last selected game in the Listbox gets updated with the info
        from the Add/Update Game entries.
        """
        if not self.cur_game.name:
            return
        # gets entered game info
        game_name = self.GameNameEntry.get()
        save_location = self.GameSaveEntry.get().replace("/", "\\")
        if os.path.exists(save_location):
            old_backup = self.cur_game.backup_path
            self.database.update(self.cur_game.name, game_name, save_location)
            # error when path is changed
            print(old_backup)
            print(self.cur_game.backup_path)
            os.rename(old_backup, self.cur_game.backup_path)
            # updates listbox entry for game
            if len(self.game_listbox.curselection()) != 0:
                index = self.game_listbox.curselection()
            else:
                index = 0
            self.game_listbox.delete(Tk.ACTIVE)
            self.game_listbox.insert(index, game_name)
        else:
            msg = "Save Location does not exist."
            messagebox.showwarning(title=self.title, message=msg)

    @staticmethod
    def readable_time_since(
        since_date: dt.datetime | str, checked_date: dt.datetime | None = None
    ):
        """
        Converts into time since for the given datetime object given
        as `since_date`.

        Examples:

        1.2 seconds ago | 3.4 minutes ago | 5.6 hours ago | 7.8 days ago
        | 9.1 months ago | 10.1 years ago

        `since_date`: Past date
        `checked_date`: Current or more recent date (Optional) defaults to
        current date if not given.
        """
        if not checked_date:
            checked_date = dt.datetime.now()
        if type(since_date) == str:
            since_date = dt.datetime.strptime(since_date, "%Y/%m/%d %H:%M:%S")
        if not isinstance(since_date, dt.datetime):
            raise Exception("Incorrect since_date given")
        seconds = (
            checked_date - since_date
        ).total_seconds()  # converts datetime object into seconds
        if seconds <= 0:
            raise Exception(
                "Invalid Response - since_date takes place after the checked date."
            )
        minutes = seconds / 60  # seconds in a minute
        hours = seconds / 3600  # minutes in a hour
        days = seconds / 86400  # hours in a day
        months = seconds / (30 * 24 * 60 * 60)  # days in an average month rounded down
        years = seconds / dt.timedelta(days=365).total_seconds()  # months in a year
        if years >= 1:
            s = "" if round(years, 2) == 1 else "s"
            return f"{round(years, 1)} year{s} ago"
        if months >= 1:
            s = "" if months == 1 else "s"
            return f"{round(months, 1)} month{s} ago"
        if days >= 1:
            s = "" if days == 1 else "s"
            return f"{round(days, 1)} day{s} ago"
        if hours >= 1:
            s = "" if hours == 1 else "s"
            return f"{round(hours, 1)} hour{s} ago"
        if minutes >= 1:
            s = "" if minutes == 1 else "s"
            return f"{round(minutes, 1)} minute{s} ago"
        else:
            return f"{round(seconds, 1)} seconds ago"

    def toggle_buttons(self, action=""):
        """
        Disables all buttons within the buttons list.
        """
        if action == "disable":
            buttons = [
                self.ExploreBackupButton,
                self.ExploreSaveButton,
                self.BackupButton,
                self.RestoreButton,
            ]
            for button in buttons:
                button.config(state="disabled")
        else:
            # enables buttons that should be enabled if a game is selected
            for button in [self.BackupButton, self.ExploreSaveButton]:
                button.config(state="normal")
            # emables buttons that should be enabled if the selected game has a backup folder otherwise disables
            if os.path.isdir(self.cur_game.backup_path):
                set_state = "normal"
            else:
                set_state = "disabled"
            for button in [self.ExploreBackupButton, self.RestoreButton]:
                button.config(state=set_state)

    def update_listbox(self, data=None):
        """
        Deletes current listbox items and adds the given data in.
        """
        if data is None:
            # refreshes the value of sorted_list
            data = self.sorted_list
        self.game_listbox.delete(0, Tk.END)
        for item in data:
            self.game_listbox.insert(Tk.END, item)
        msg = "Select a Game\nto continue\n"
        self.set_info_text(msg=msg)
        # updates title info label
        total_backup_size = get_dir_size(self.cfg.backup_folder)
        info_text = (
            f"Total Games: {len(self.sorted_list)}\n"
            f"Total Backup Size: {total_backup_size}"
        )
        self.Title.config(text=info_text)
        self.toggle_buttons("disable")

    def entry_search(self, _):
        """
        Finds all items in the sorted_list that have the search box data in it.
        It then updates the listbox data to only include matching results.
        """

        # TODO test to be sure threading here does not cause issues.
        def search():
            typed = self.search_entry.get()
            if typed == "":
                data = self.sorted_list
            else:
                data = [
                    item for item in self.sorted_list if typed.lower() in item.lower()
                ]
            self.update_listbox(data)

        Thread(target=search, daemon=True).start()

    def select_entry(self, _):
        """
        Deletes only search box default text on click.
        """
        if self.search_entry.get() == self.default_entry_value:
            self.search_entry.delete(0, Tk.END)

    def listbox_nav(self, e):
        """
        Allows Up and Down arrow keys to navigate the listbox.
        """
        index = self.game_listbox.curselection()[0]
        if e.keysym == "Up":
            index += -1
        if e.keysym == "Down":
            index += 1
        if 0 <= index < self.game_listbox.size():
            self.game_listbox.selection_clear(0, Tk.END)
            self.game_listbox.select_set(index)
            self.game_listbox.selection_anchor(index)
            self.game_listbox.activate(index)

    def unfocus_entry(self):
        """
        Resets search box to default_entry_value when it loses focus.
        """
        self.search_entry.delete(0, Tk.END)
        self.search_entry.insert(0, self.default_entry_value)

    def select_listbox_entry(self, Update=0):
        """
        Updates Game Data into Name and Save Entry for viewing.
        Allows for updating specific entries in the database as well.

        Arguments:

        Update -- 1 or 0 (default = 0)
        """
        selection = self.game_listbox.curselection()
        listbox_selection = self.game_listbox.get(selection[0])
        self.cur_game = self.database.get(listbox_selection)
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
            self.GameNameEntry.insert(0, self.cur_game.name)
            self.GameSaveEntry.insert(0, self.cur_game.save_location)
            # search box update
            self.search_entry.delete(0, Tk.END)
            self.search_entry.insert(0, self.default_entry_value)
            # enables all buttons to be pressed once a selection is made
            self.toggle_buttons()
            if self.cur_game.last_backup == "Never":
                msg = f"{self.cur_game.name} has not been backed up\n\n"
            elif not os.path.exists(self.cur_game.save_location):
                print(self.cur_game)
                msg = f"{self.cur_game.name} Save Location Is Missing\n"
            else:
                time_since = self.readable_time_since(self.cur_game.last_backup)
                if os.path.exists(self.cur_game.backup_path):
                    total_backups = len(os.listdir(self.cur_game.backup_path))
                else:
                    total_backups = 0
                msg = (
                    f"{self.cur_game.name}\n"
                    f"Last backed up {time_since}\n"
                    f"Game Backup Size: {self.cur_game.backup_size} from {total_backups} backups"
                )
            self.set_info_text(msg=msg)
            self.BackupButton.focus_set()

    def exit_program(self):
        """
        Closes the database and quits the program when closing the interface.
        """
        if self.backup_restore_in_progress:
            msg = f"Backup/Restore in progress.\n{self.title} will close after completion when you close this message."
            self.set_info_text(msg=msg)

        while self.backup_restore_in_progress:
            time.sleep(0.05)
        # BUG interface fails to exit if filedialog is left open
        # fix using subclassed filedialog commands that can close it
        self.root.withdraw()
        self.database.close_database()
        sys.exit()

    def open_interface_window(self):
        """
        Opens the main Game Save Manager interface.
        """
        start = time.perf_counter()
        # Defaults
        BoldBaseFont = "Arial Bold"
        self.root = Tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.exit_program)
        window_width = 680
        window_height = 550
        self.tk_window_options(self.root, window_width, window_height)
        # self.root.geometry(f'{window_width}x{window_height}+{width}+{height}')

        # binding
        if self.cfg.quick_backup:
            self.root.bind("<Return>", self.backup_shortcut)

        # Main Row 0
        Backup_Frame = Tk.Frame(self.root)
        Backup_Frame.grid(columnspan=4, column=0, row=0, padx=(20, 20), pady=(5, 0))

        self.Title = Tk.Label(Backup_Frame, text="\n", font=(BoldBaseFont, 10))
        self.Title.grid(columnspan=4, row=0, column=1)

        button_width = 23
        self.BackupButton = ttk.Button(
            Backup_Frame,
            text="Backup Save",
            state="disabled",
            command=self.run_full_backup,
            width=button_width,
        )
        self.BackupButton.grid(row=3, column=1, padx=5, pady=5)

        self.RestoreButton = ttk.Button(
            Backup_Frame,
            text="Restore Save",
            state="disabled",
            command=self.restore_save,
            width=button_width,
        )
        self.RestoreButton.grid(row=3, column=2, padx=5)

        self.ExploreSaveButton = ttk.Button(
            Backup_Frame,
            text="Explore Save Location",
            state="disabled",
            command=lambda: self.explore_folder("Game Save"),
            width=button_width,
        )
        self.ExploreSaveButton.grid(row=4, column=1, padx=5)

        self.ExploreBackupButton = ttk.Button(
            Backup_Frame,
            text="Explore Backup Location",
            state="disabled",
            command=lambda: self.explore_folder("Backup"),
            width=button_width,
        )
        self.ExploreBackupButton.grid(row=4, column=2, padx=5)

        # Main Row 1
        instruction = "Select a Game\nto continue"
        self.ActionInfo = Tk.Label(self.root, text=instruction, font=(BoldBaseFont, 10))
        self.ActionInfo.grid(columnspan=4, row=1, column=0, padx=5, pady=5)
        # Main Row 2
        self.ListboxFrame = Tk.Frame(self.root)
        self.ListboxFrame.grid(
            columnspan=4, row=2, column=0, padx=(20, 20), pady=(5, 10)
        )

        self.scrollbar = Tk.Scrollbar(self.ListboxFrame, orient=Tk.VERTICAL)
        self.scrollbar.grid(row=1, column=3, sticky="ns", rowspan=3)

        self.search_entry = ttk.Entry(
            self.ListboxFrame, width=89, exportselection=False
        )
        self.search_entry.grid(columnspan=3, row=0, column=0, pady=(0, 3))
        self.search_entry.insert(0, self.default_entry_value)
        self.search_entry.bind("<1>", self.select_entry)
        # TODO fix this
        # self.search_entry.bind("<FocusOut>", self.unfocus_entry)
        self.search_entry.bind("<KeyRelease>", self.entry_search)

        self.game_listbox = Tk.Listbox(
            self.ListboxFrame,
            exportselection=False,
            yscrollcommand=self.scrollbar.set,
            font=(BoldBaseFont, 12),
            height=10,
            width=60,
        )
        self.game_listbox.grid(columnspan=3, row=1, column=0)
        self.game_listbox.bind(
            "<<ListboxSelect>>",
            lambda event, game_listbox=self.game_listbox,: self.select_listbox_entry(1),
        )

        # WIP finish or delete up and down control of listbox
        # full interface bind for lisxtbox navigation
        # self.root.bind('<Up>', lambda event,arg=.1:self.listbox_nav(event))
        # self.root.bind('<Down>', lambda event,arg=.1:self.listbox_nav(event))

        # scrollbar config
        self.scrollbar.config(command=self.game_listbox.yview)
        # listbox fill
        self.sorted_list = self.database.sorted_games()
        self.update_listbox()

        # Main Row 3
        Add_Game_Frame = Tk.LabelFrame(self.root, text="Manage Games")
        Add_Game_Frame.grid(columnspan=4, row=3, padx=15, pady=(5, 17))

        EnterGameLabel = ttk.Label(Add_Game_Frame, text="Game Name")
        EnterGameLabel.grid(row=0, column=0)

        entry_width = 65
        self.GameNameEntry = ttk.Entry(
            Add_Game_Frame, width=entry_width, exportselection=False
        )
        self.GameNameEntry.grid(row=0, column=1, columnspan=3, pady=8, padx=5)

        EnterSaveLabeL = ttk.Label(Add_Game_Frame, text="Save Location")
        EnterSaveLabeL.grid(row=1, column=0)

        self.GameSaveEntry = ttk.Entry(
            Add_Game_Frame, width=entry_width, exportselection=False
        )
        self.GameSaveEntry.grid(row=1, column=1, columnspan=3, pady=5, padx=10)

        browse_button_width = 13

        BrowseButton = ttk.Button(
            Add_Game_Frame,
            text="Browse",
            width=browse_button_width,
            command=self.browse,
        )
        BrowseButton.grid(row=1, column=4, padx=10)

        # Button Frame Row 2
        Button_Frame = Tk.Frame(Add_Game_Frame)
        Button_Frame.grid(columnspan=5, row=2, pady=(5, 5))

        button_padx = 4
        button_pady = 5
        ConfirmAddButton = ttk.Button(
            Button_Frame, text="Add Game", command=self.add_game_to_database, width=16
        )
        ConfirmAddButton.grid(row=2, column=0, padx=button_padx, pady=button_pady)

        UpdateButton = ttk.Button(
            Button_Frame, text="Update Game", command=self.update_game, width=16
        )
        UpdateButton.grid(row=2, column=1, padx=button_padx, pady=button_pady)

        RemoveButton = ttk.Button(
            Button_Frame, text="Remove Game", command=self.delete_game, width=16
        )
        RemoveButton.grid(row=2, column=2, padx=button_padx, pady=button_pady)

        ClearButton = ttk.Button(
            Button_Frame,
            text="Clear Entries",
            command=self.select_listbox_entry,
            width=16,
        )
        ClearButton.grid(row=2, column=3, padx=button_padx, pady=button_pady)

        ClearButton = ttk.Button(
            Button_Frame, text="Refresh Games", command=self.update_listbox, width=16
        )
        ClearButton.grid(row=2, column=4, padx=button_padx, pady=button_pady)

        # interface startup time check
        end = time.perf_counter()
        start_elapsed = round(end - start, 2)
        if start_elapsed > 0.5:
            print("Interface Ready: ", start_elapsed)
        self.root.mainloop()

    def run(self):
        """
        Runs everything needed to make the program work.
        """
        if self.cfg.output:
            sys.stdout = open("output.txt", "w")
        self.backup_folder_check()
        # opens the interface
        self.open_interface_window()
        if self.cfg.output:
            sys.stdout.close()


if __name__ == "__main__":
    save_manager = SaveManager()
    save_manager.run()
