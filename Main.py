from logging.handlers import RotatingFileHandler
from tkinter import messagebox, filedialog
from functools import partial
from tkinter import ttk
import datetime as dt
import tkinter as Tk
import logging as lg
import configparser
import threading
import sqlite3
import shutil
import math
import time
import re
import os

def main():
    log_formatter = lg.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%m-%d-%Y %I:%M:%S %p')
    logger = lg.getLogger(__name__)
    logger.setLevel(lg.DEBUG)
    my_handler = RotatingFileHandler('Game_Backup.log', maxBytes=5*1024*1024, backupCount=2)
    my_handler.setFormatter(log_formatter)
    logger.addHandler(my_handler)

    Config = configparser.ConfigParser()
    Config.read('Config.ini')
    backup_dest = Config.get('Main', 'backup_dest')
    backup_redundancy = int(Config.get('Main', 'backup_redundancy'))

    game_list = sqlite3.connect('game_list.db')
    c = game_list.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS games (
    game_name text,
    save_location text,
    last_backup text
    )''')


    def Database_Check(): #  TODO Finish function to make sure save locations exist.
        '''Checks for missing save directories from database.'''
        c = game_list.cursor()
        c.execute("SELECT save_location FROM games")
        missing_save_loc = []
        for save_location in c.fetchall():
            if os.path.isdir(save_location[0]):
                pass
            else:
                missing_save_loc.append(save_location[0])
        missing_saves = len(missing_save_loc)
        continue_var = 0
        if missing_saves > 0 and missing_saves < 6:
            msg = f'Save Locations for the following do not exist.\n{missing_save_loc}'
            continue_var = messagebox.showwarning(title='Game Save Manager', message=msg)
        elif len(missing_save_loc) > 5:
            msg = 'More then 5 save locations do not exist.'
            continue_var = messagebox.showwarning(title='Game Save Manager', message=msg)


    def sanitize_for_filename(string):
        '''Removes illegal characters from string so it can become a valid filename.'''
        for char in ('<', '>', ':', '/', '\\', '|', '?', '*'):
            string = string.replace(char,'')
        return string


    def Get_Save_Loc(game):
        '''Returns the save location of the entered game from the SQLite Database.'''
        print(f'Getting Save location for {game}.')
        game_list = sqlite3.connect('game_list.db')
        c = game_list.cursor()
        c.execute("SELECT save_location FROM games WHERE game_name=:game_name", {'game_name': game})
        save_location = c.fetchone()[0]
        return save_location


    def Game_list_Sorted():
        '''Sorts the game list from the SQLite database based on the last backup and then returns a list.'''
        c = game_list.cursor()
        c.execute("SELECT game_name FROM games ORDER BY last_backup DESC")
        ordered_games = []
        for game_name in c.fetchall():
            ordered_games.append(game_name[0])
        game_list.commit()
        return ordered_games


    def Delete_Oldest(game):
        '''Deletest the oldest saves so only the the newest specified ammount is left.'''
        saves_list = []
        dir = os.path.join(backup_dest, game)
        print(dir)
        for file in os.listdir(dir):
            file = os.path.join(dir, file)
            saves_list.append(file)
        if len(saves_list) < 4:
            print(f'{backup_redundancy} or Less Saves.')
            return
        else:
            print(f'More then {backup_redundancy} Saves.')
            sorted_list = sorted(saves_list, key=os.path.getctime, reverse=True)
            for i in range(backup_redundancy, len(saves_list)):
                shutil.rmtree(sorted_list[i])

    def Save_Backup(game):
        '''Backups up the game entered based on SQLite save location data to the specified backup folder.'''
        current_time = dt.datetime.now().strftime("%d-%m-%y %H-%M")
        save_loc = Get_Save_Loc(game)
        game = sanitize_for_filename(game)
        dest = os.path.join(backup_dest, game, current_time)
        try:
            shutil.copytree(save_loc, dest)
            Delete_Oldest(game)
        except FileNotFoundError:
            print('No Action Completed - File location does not exist.')
        except FileExistsError:
            print('No Action Completed - Save Already Backed up.')
        c = game_list.cursor()
        c.execute("""UPDATE games SET last_backup = :last_backup WHERE game_name = :game_name""",
        {'game_name': game, 'last_backup': dt.datetime.now()})
        game_list.commit()
        logger.debug(f'Backed-up Save for {game}.')


    def Refresh_Dropdown():
        '''Refreshes dropdown contents in cases changes were made to its lists.'''
        popupMenu['menu'].delete(0, 'end')
        updated_list = Game_list_Sorted()
        for game in updated_list:
            popupMenu['menu'].add_command(label=game, command=Tk._setit(clicked, game))
        clicked.set(updated_list[0])


    def Restore_Backup(game): # TODO Finish Restore
        '''Restores game save after moving current save to special backup folder.'''
        dest = os.path.join(backup_dest, game, 'Pre-Restore Backup')
        save_loc = Get_Save_Loc(game)
        # try:
        #     shutil.move(save_loc, dest)
        # except FileNotFoundError:
        #     messagebox.showwarning(title='Game Save Manager', message='Save Location does not exist.')
        Create_Restore_Game_Window(game)
        to_restore = save_to_restore.get()
        shutil.copytree(to_restore, save_loc)
        logger.debug(f'Restored Save for {game}.')


    def Delete_Game_from_DB(game):
        '''Deletes selected game from SQLite Database.'''
        c = game_list.cursor()
        c.execute("DELETE FROM games WHERE game_name = :game_name", {'game_name': game})
        game_list.commit()
        Refresh_Dropdown()
        logger.debug(f'Deleted {game} from database.')


    def Add_Game_Window():

        def Add_Game_Pressed():
            game_name = GameNameEntry.get()
            save_location = GameSaveEntry.get()
            if os.path.isdir(save_location):
                GameSaveEntry.delete(0, Tk.END)
                GameNameEntry.delete(0, Tk.END)
                Add_Game_to_DB(game_name, save_location)
            else:
                messagebox.showwarning(title='Game Save Manager', message='Save Location does not exist.')


        def Browse_Click():
            save_dir = Tk.filedialog.askdirectory(initialdir="C:/", title="Select Save Directory")
            GameSaveEntry.delete(0, Tk.END)
            GameSaveEntry.insert(0, save_dir)


        def Add_Game_to_DB(game, save_location):
            '''Adds game to SQLite Database using entry box data.'''
            c = game_list.cursor()
            c.execute("INSERT INTO games VALUES (:game_name, :save_location, :last_backup)",
            {'game_name': game, 'save_location': save_location, 'last_backup': dt.datetime.now()})
            game_list.commit()
            logger.debug(f'Added {game} to database.')
            Refresh_Dropdown()
            Add_Game_Window.destroy()


        def Update_Game(): # TODO Add button to update game info.
            '''Allows updating data for games in database.'''
            pass


        def Cancel_Pressed():
            Add_Game_Window.destroy()


        Add_Game_Window = Tk.Toplevel(takefocus=True)
        Add_Game_Window.title('Game Save Manager - Add Game')
        Add_Game_Window.iconbitmap('Save_Icon.ico')
        Add_Game_Window.resizable(width=False, height=False)
        Add_Game_Window.bind_class("Button", "<Key-Return>", lambda event: event.widget.invoke())
        Add_Game_Window.unbind_class("Button", "<Key-space>")

        EnterGameLabeL = ttk.Label(Add_Game_Window, text='Enter Game Name')
        EnterGameLabeL.grid(row=0, column=0)

        GameNameEntry = ttk.Entry(Add_Game_Window, width=70, exportselection=0)
        GameNameEntry.grid(row=0, column=1, columnspan=3, pady=10, padx=5)

        EnterSaveLabeL = ttk.Label(Add_Game_Window, text='Enter Save Location')
        EnterSaveLabeL.grid(row=1, column=0)

        GameSaveEntry = ttk.Entry(Add_Game_Window, width=70, exportselection=0)
        GameSaveEntry.grid(row=1, column=1, columnspan=3, pady=5, padx=5)

        ConfirmButton = ttk.Button(Add_Game_Window, text='Confirm', command=Add_Game_Pressed, width=20)
        ConfirmButton.grid(row=2, column=0, padx=5, pady= 5)

        ClearButton = ttk.Button(Add_Game_Window, text='Clear', command=Add_Game_Pressed, width=20)
        ClearButton.grid(row=2, column=1, padx=5, pady= 5)

        BrowseButton = ttk.Button(Add_Game_Window, text='Browse', command=Browse_Click, width=20)
        BrowseButton.grid(row=2, column=2, padx=5, pady= 5)

        CancelButton = ttk.Button(Add_Game_Window, text='Cancel', command=Cancel_Pressed, width=20)
        CancelButton.grid(row=2, column=3, padx=5, pady= 5)

        Add_Game_Window.mainloop()

    def Create_Restore_Game_Window(game):

        backup_list =[]
        backup = os.path.join(backup_dest, game)
        for file in os.listdir(backup):
            backup_list.append(file)


        def Cancel_Pressed():
            Restore_Game_Window.destroy()

        def Restore_Game_Pressed():
            save_to_restore = save_to_restore.get()


        Restore_Game_Window = Tk.Toplevel(takefocus=True)
        Restore_Game_Window.title('Game Save Manager - Restore Game')
        Restore_Game_Window.iconbitmap('Save_Icon.ico')
        Restore_Game_Window.resizable(width=False, height=False)
        Restore_Game_Window.bind_class("Button", "<Key-Return>", lambda event: event.widget.invoke())
        Restore_Game_Window.unbind_class("Button", "<Key-space>")

        save_to_restore = Tk.StringVar(Restore_Game_Window)

        RestoreInfo = ttk.Label(Restore_Game_Window, text=f'Select save to restore for {game}.')
        RestoreInfo.grid(columnspan=2, row=0, column=0)

        popupMenu = ttk.OptionMenu(Restore_Game_Window, save_to_restore, *backup_list)
        popupMenu.grid(columnspan=2, row=1, column=0, pady=(0,5))

        ConfirmButton = ttk.Button(Restore_Game_Window, text='Confirm', command=Restore_Game_Pressed, width=20)
        ConfirmButton.grid(row=2, column=0, padx=5, pady= 5)

        CancelButton = ttk.Button(Restore_Game_Window, text='Cancel', command=Cancel_Pressed, width=20)
        CancelButton.grid(row=2, column=1, padx=5, pady= 5)

        Restore_Game_Window.mainloop()


    # Defaults for Background and fonts
    Background = 'White'
    BoldBaseFont = "Arial Bold"
    BaseFont = "Arial"

    Main_GUI = Tk.Tk()
    Main_GUI.title('Game Save Manager')
    Main_GUI.iconbitmap('Save_Icon.ico')
    Main_GUI.resizable(width=False, height=False)
    Main_GUI.bind_class("Button", "<Key-Return>", lambda event: event.widget.invoke())
    Main_GUI.unbind_class("Button", "<Key-space>")

    Backup_Frame = Tk.Frame(Main_GUI)
    Backup_Frame.grid(columnspan=4, row=0,  padx=(20, 20), pady=(5, 10))


    def convert_size(backup_dest):
        '''Converts size of directory best fitting '''
        size_bytes = os.path.getsize(backup_dest)
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f'{s} {size_name[i]}'


    info_text = f'Total Games in Database: {len(Game_list_Sorted())}\nSize of Backup: {convert_size(backup_dest)}'
    Title = Tk.Label(Backup_Frame, text=info_text, font=(BoldBaseFont, 10))
    Title.grid(columnspan=4, row=0, column=1)

    Guide = Tk.Label(Backup_Frame, text='Selected Game:', font=(BoldBaseFont, 10))
    Guide.grid(columnspan=2, row=1, column=1, pady=(10,0))


    def Clicked_Delete():
        msg = 'Are you sure that you want to delete the game?'
        Delete_Check = messagebox.askyesno(title='Game Save Manager', message=msg)
        if Delete_Check:
          Delete_Game_from_DB(clicked.get())


    clicked = Tk.StringVar(Main_GUI)
    sorted_list = Game_list_Sorted()
    clicked.set(sorted_list[0]) # set the default option

    popupMenu = ttk.OptionMenu(Backup_Frame, clicked, *sorted_list)
    popupMenu.grid(columnspan=2, row=2, column=1, pady=(0,5))

    BackupButton = ttk.Button(Backup_Frame, text='Backup Game Save', command=partial(Save_Backup, clicked.get()), width=20)
    BackupButton.grid(row=3, column=1, padx=5, pady= 5)

    RestoreButton = ttk.Button(Backup_Frame, text='Restore Game Save', command=partial(Restore_Backup, clicked.get()), width=20)
    RestoreButton.grid(row=3, column=2, padx=5, pady= 5)

    DeleteButton = ttk.Button(Backup_Frame, text='Delete Selected Game', command=Clicked_Delete, width=20)
    DeleteButton.grid(row=4, column=1, padx=5, pady= 5)

    AddButton = ttk.Button(Backup_Frame, text='Add New Game', command=Add_Game_Window, width=20)
    AddButton.grid(row=4, column=2, padx=5, pady= 5)

    Database_Check()

    Main_GUI.mainloop()
    game_list.close()

if __name__ == '__main__':
    main()
