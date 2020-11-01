from os import stat
from tkinter import filedialog, messagebox
from tkinter import ttk
import tkinter as Tk
import datetime as dt
import logging as lg
import shutil
import math
import json
import os


class Backup:
    def __init__(self, database, logger):
        with open('settings.json') as json_file:
            data = json.load(json_file)
        self.backup_dest = data['settings']['backup_dest']
        self.backup_redundancy = data['settings']['backup_redundancy']
        if self.backup_redundancy > 4:
            self.backup_redundancy = 4
        self.disable_resize = data['settings']['disable_resize']
        self.database = database
        self.cursor = self.database.cursor()
        self.logger = logger
        self.selected_game = None


    def Database_Check(self):
        '''Checks for missing save directories from database.'''
        self.cursor.execute("SELECT save_location FROM games")
        missing_save_loc = []
        for save_location in self.cursor.fetchall():
            if not os.path.isdir(save_location[0]):
                missing_save_loc.append(save_location[0])
        missing_saves = len(missing_save_loc)
        if missing_saves > 0 and missing_saves < 6:
            msg = f'Save Locations for the following do not exist.\n{missing_save_loc}'
            messagebox.showwarning(title='Game Save Manager', message=msg)
            self.logger.debug(f'Missing Save Locations:{missing_save_loc}')
        elif len(missing_save_loc) > 5:
            msg = 'More than 5 save locations do not exist.'
            messagebox.showwarning(title='Game Save Manager', message=msg)
            self.logger.debug(f'More then 4 save locations in the database do not exist.')


    def Sanitize_For_Filename(self, string):
        '''Removes illegal characters from string so it can become a valid filename.'''
        for char in ('<', '>', ':', '/', '\\', '|', '?', '*'):
            string = string.replace(char,'')
        return string


    def Get_Save_Loc(self, game):
        '''Returns the save location of the entered game from the SQLite Database.'''
        self.cursor.execute("SELECT save_location FROM games WHERE game_name=:game_name", {'game_name': game})
        save_location = self.cursor.fetchone()[0]
        return save_location


    def Game_list_Sorted(self):
        '''Sorts the game list from the SQLite database based on the last backup and then returns a list.'''
        self.cursor.execute("SELECT game_name FROM games ORDER BY last_backup DESC")
        ordered_games = []
        for game_name in self.cursor.fetchall():
            ordered_games.append(game_name[0])
        self.database.commit()
        return ordered_games


    # def Delete_Folder(self, dir, delete_oldest=0, n=3):
    #     '''Deletes the entered directory and all of its contents.

    #     Arguements:

    #     dir -- directory to be deleted

    #     delete_oldest -- 1 enables delete oldest files , 0 disables (default = 0)

    #     n -- deleted oldest folders until nth new files are left (default = 3)
    #     '''
    #     # TODO finish new function
    #     saves_list = []
    #     for file in os.scandir(dir):
    #         saves_list.append(file.path)
    #     if len(saves_list) < self.backup_redundancy and delete_oldest == 1:
    #         self.logger.info(f'{game} has {self.backup_redundancy} or Less Saves.')
    #         return
    #     else:
    #         sorted_list = sorted(saves_list, key=os.path.getctime, reverse=True)
    #         for i in range(self.backup_redundancy, len(saves_list)):
    #             shutil.rmtree(sorted_list[i])
    #         self.logger.info(f'{game} had more then {self.backup_redundancy} Saves. Deleted oldest saves.')


    def Delete_Oldest(self, game):
        '''Deletest the oldest saves so only the the newest specified ammount is left.'''
        saves_list = []
        dir = os.path.join(self.backup_dest, game)
        for file in os.listdir(dir):
            file = os.path.join(dir, file)
            saves_list.append(file)
        if len(saves_list) < 4:
            self.logger.info(f'{game} has {self.backup_redundancy} or Less Saves.')
            return
        else:
            sorted_list = sorted(saves_list, key=os.path.getctime, reverse=True)
            for i in range(self.backup_redundancy, len(saves_list)):
                shutil.rmtree(sorted_list[i])
            self.logger.info(f'{game} had more then {self.backup_redundancy} Saves. Deleted oldest saves.')


    def Save_Backup(self, game, info_label):
        '''Backups up the game entered based on SQLite save location data to the specified backup folder.'''
        current_time = dt.datetime.now().strftime("%d-%m-%y %H-%M-%S")
        save_loc = self.Get_Save_Loc(game)
        game = self.Sanitize_For_Filename(game)
        dest = os.path.join(self.backup_dest, game, current_time)
        try:
            shutil.copytree(save_loc, dest)
            self.Delete_Oldest(game)
            info_label.config(text=f'Backed up {game} to set backup destination.\n')
        except FileNotFoundError:
            messagebox.showwarning(title='Game Save Manager', message='Action Failed - File location does not exist.')
        except FileExistsError:
            messagebox.showwarning(title='Game Save Manager', message='Action Failed - Save Already Backed up.')
        last_backup = dt.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        self.cursor.execute("""UPDATE games SET last_backup = :last_backup WHERE game_name = :game_name""",
        {'game_name': game, 'last_backup': last_backup})
        self.database.commit()
        self.logger.info(f'Backed-up Save for {game}.')


    def Restore_Backup(self):
        '''Restores game save after renaming current save folder to "save.old".'''
        backup_list =[]
        selected_game = self.selected_game
        backup_path = os.path.join(self.backup_dest, self.selected_game)
        save_location = self.Get_Save_Loc(self.selected_game)
        print(save_location)
        if os.path.exists(backup_path):
            for file in os.scandir(backup_path):
                backup_list.append(file)
            print(backup_list)
        else:
            messagebox.showwarning(title='Game Save Manager', message='No saves exist for this game.')
            return


        def Restore_Game_Pressed():
            save_name = save_listbox.get(save_listbox.curselection())
            save_path = os.path.join(self.backup_dest, selected_game, save_name)
            if os.path.exists(f'{save_location}.old'):
                msg = '''Backup of current save before last restore already exists.
                    \nDo you want to delete it? This will cancel the restore.'''
                response = messagebox.askyesno(title='Game Save Manager', message=msg)
                if response in ['yes', 'y']:
                    shutil.rmtree(f'{save_location}.old')
                    # os.removedirs(f'{save_location}.old')
                else:
                    print('Canceling Restore.')
                    return
            os.rename(save_location, f'{save_location}.old')
            shutil.copytree(save_path, save_location)
            self.logger.info(f'Restored Save for {selected_game}.')
            Restore_Game_Window.destroy()


        Restore_Game_Window = Tk.Toplevel(takefocus=True)
        Restore_Game_Window.title('Game Save Manager - Restore Game')
        Restore_Game_Window.iconbitmap('Save_Icon.ico')
        Restore_Game_Window.resizable(width=False, height=False)
        # Restore_Game_Window.geometry("+600+600")
        Restore_Game_Window.bind_class("Button", "<Key-Return>", lambda event: event.widget.invoke())
        Restore_Game_Window.unbind_class("Button", "<Key-space>")

        RestoreInfo = ttk.Label(Restore_Game_Window,
            text=f'Select Save for {self.selected_game}', font=("Arial Bold", 10))
        RestoreInfo.grid(columnspan=2, row=0, column=0, pady=(2, 0))

        save_listbox = Tk.Listbox(Restore_Game_Window, exportselection=False, font=("Arial Bold", 12), height=5, width=30)
        save_listbox.grid(columnspan=2, row=1, column=0, pady=5, padx=5)

        for item in backup_list:
            save_listbox.insert(Tk.END, item.name)

        confirm_button = ttk.Button(Restore_Game_Window, text='Confirm', command=Restore_Game_Pressed, width=20)
        confirm_button.grid(row=2, column=0, padx=5, pady= 5)

        CancelButton = ttk.Button(Restore_Game_Window, text='Cancel', command=Restore_Game_Window.destroy, width=20)
        CancelButton.grid(row=2, column=1, padx=5, pady= 5)

        Restore_Game_Window.mainloop()

    def Convert_Size(self, directory):
        '''Converts size of directory best fitting '''
        total_size = 0
        for path, dirs, files in os.walk(directory):
            for f in files:
                fp = os.path.join(path, f)
                total_size += os.path.getsize(fp)
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(total_size, 1024)))
        p = math.pow(1024, i)
        s = round(total_size / p, 2)
        return f'{s} {size_name[i]}'


    def Add_Game_Pressed(self, GameNameEntry, GameSaveEntry, Listbox):
        game_name = GameNameEntry.get()
        save_location = GameSaveEntry.get()
        if os.path.isdir(save_location):
            GameSaveEntry.delete(0, Tk.END)
            GameNameEntry.delete(0, Tk.END)
            self.Add_Game_to_DB(game_name, save_location)
            Listbox.insert(0, game_name)
        else:
            messagebox.showwarning(title='Game Save Manager', message='Save Location does not exist.')


    def Browse_For_Save(self, GameNameEntry, GameSaveEntry):
        save_dir = filedialog.askdirectory(initialdir="C:/", title="Select Save Directory")
        GameSaveEntry.delete(0, Tk.END)
        GameSaveEntry.insert(0, save_dir)


    def Add_Game_to_DB(self, game, save_location):
        '''Adds game to SQLite Database using entry box data.'''
        self.cursor.execute("INSERT INTO games VALUES (:game_name, :save_location, :last_backup)",
        {'game_name': game, 'save_location': save_location, 'last_backup': dt.datetime.now()})
        self.database.commit()
        self.logger.info(f'Added {game} to database.')


    def Delete_Game_from_DB(self, Listbox):
        '''Deletes selected game from SQLite Database.'''
        msg = 'Are you sure that you want to delete the game?'
        Delete_Check = messagebox.askyesno(title='Game Save Manager', message=msg)
        if Delete_Check:
            self.cursor.execute("DELETE FROM games WHERE game_name = :game_name", {'game_name': self.selected_game})
            self.database.commit()
            selected_game = Listbox.curselection()
            Listbox.delete(selected_game[0])
            msg = 'Do you want to delete the backed up game saves as well?'
            response = messagebox.askyesno(title='Game Save Manager', message=msg)
            if ['yes, y', 1] in response:
                print('WIP')
            self.logger.info(f'Deleted {self.selected_game} from database.')


    def Update_Game(self, GameNameEntry, GameSaveEntry, listbox):
        '''Allows updating data for games in database.
        The last selected game in the Listbox gets updated with the info from the Add/Update Game entries.'''
        game_name = GameNameEntry.get()
        save_location = GameSaveEntry.get()
        if os.path.isdir(save_location):
            sql_update_query  ='''UPDATE games
                    SET game_name = ?, save_location = ?
                    WHERE game_name = ?;'''
            data = (game_name, save_location, self.selected_game)
            self.cursor.execute(sql_update_query , data)
            self.database.commit()
            os.rename(os.path.join(self.backup_dest, self.selected_game), os.path.join(self.backup_dest, game_name))
            # TODO delete then readd selected entry
            listbox.delete(0 , Tk.ACTIVE)
            listbox.insert(0, game_name)
            self.logger.info(f'Updated {self.selected_game} in database.')
        else:
            msg = f'Save Location does not exist.'
            messagebox.showwarning(title='Game Save Manager', message=msg)


    def Delete_Update_Entry(self, listbox, GameSaveEntry, GameNameEntry, ActionInfo, Update=0):
        '''Updates Game Data into Name and Save Entry for viewing.
        Allows for updating specific entries in the database as well.'''
        # clears entry boxes
        GameNameEntry.delete(0, Tk.END)
        GameSaveEntry.delete(0, Tk.END)
        # updates entry boxes to show currently selected game in listbox
        if Update == 1:
            self.selected_game = listbox.get(listbox.curselection())  # script wide variable for selected game
            GameNameEntry.insert(0, self.selected_game)
            GameSaveEntry.insert(0, self.Get_Save_Loc(self.selected_game))
            self.cursor.execute("SELECT last_backup FROM games WHERE game_name=:game_name", {'game_name': self.selected_game})
            last_update = self.cursor.fetchone()[0]
            ActionInfo.config(text=f'{self.selected_game} last updated on {last_update}\nTotal Backup Space: {self.Convert_Size(os.path.join(self.backup_dest, self.selected_game))}')
