from logging.handlers import RotatingFileHandler
from tkinter import ttk
import datetime as dt
import tkinter as Tk
import logging as lg
import configparser
import threading
import shutil
import math
import time
import re
import os
import sqlite3
from Backup_Class import Backup

def main():
    log_formatter = lg.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%m-%d-%Y %I:%M:%S %p')
    logger = lg.getLogger(__name__)
    logger.setLevel(lg.DEBUG)
    my_handler = RotatingFileHandler('Game_Backup.log', maxBytes=5*1024*1024, backupCount=2)
    my_handler.setFormatter(log_formatter)
    logger.addHandler(my_handler)

    game_list = sqlite3.connect('game_list.db')
    c = game_list.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS games (
    game_name text,
    save_location text,
    last_backup text
    )''')

    App = Backup(game_list, logger)

    # Defaults for Background and fonts
    Background = 'White'
    BoldBaseFont = "Arial Bold"
    BaseFont = "Arial"


    Main_GUI = Tk.Tk()
    Main_GUI.title('Game Save Manager')
    Main_GUI.iconbitmap('Save_Icon.ico')
    window_width = 617
    window_height = 510
    width = int((Main_GUI.winfo_screenwidth()-window_width)/2)
    height = int((Main_GUI.winfo_screenheight()-window_height)/2)
    Main_GUI.geometry(f'{window_width}x{window_height}+{width}+{height}')
    Main_GUI.bind_class("Button", "<Key-Return>", lambda event: event.widget.invoke())
    Main_GUI.unbind_class("Button", "<Key-space>")

    Backup_Frame = Tk.Frame(Main_GUI)
    Backup_Frame.grid(columnspan=4, row=0,  padx=(20, 20), pady=(5, 10))

    info_text = f'Total Games in Database: {len(App.Game_list_Sorted())}\nSize of Backups: {App.Convert_Size()}'
    Title = Tk.Label(Backup_Frame, text=info_text, font=(BoldBaseFont, 10))
    Title.grid(columnspan=4, row=0, column=1)

    Guide = Tk.Label(Backup_Frame, text='Select Game', font=(BoldBaseFont, 10))
    Guide.grid(columnspan=2, row=1, column=1, pady=(10,0))

    scrollbar = Tk.Scrollbar(Backup_Frame, orient=Tk.VERTICAL)
    scrollbar.config(command=Tk.Listbox.yview)
    Listbox = Tk.Listbox(Backup_Frame, yscrollcommand=scrollbar.set, font=(BoldBaseFont, 12), height=10, width=51)
    scrollbar.grid(row=2, column=2)
    Listbox.grid(columnspan=2, row=2, column=1, pady=(0,5))

    sorted_list = App.Game_list_Sorted()
    for item in sorted_list:
        Listbox.insert(Tk.END, item)

    BackupButton = ttk.Button(Backup_Frame, text='Backup Selected Game Save',
        command=lambda: App.Save_Backup(Listbox.get(Tk.ACTIVE)), width=20)
    BackupButton.grid(row=3, column=1, padx=5, pady= 5)

    RestoreGameButton = ttk.Button(Backup_Frame, text='Restore Selected Game',
        command=lambda: App.Restore_Backup(Listbox.get(Tk.ACTIVE)), width=20)
    RestoreGameButton.grid(row=3, column=2, padx=5, pady= 5)

    RestoreSaveButton = ttk.Button(Backup_Frame, text='Restore Selected Save',
        command=lambda: App.Restore_Backup(Listbox.get(Tk.ACTIVE)), width=20, state='disabled')
    RestoreSaveButton.grid(row=4, column=2, padx=5, pady= 5)

    DeleteButton = ttk.Button(Backup_Frame, text='Delete Selected Game',
        command=lambda: App.Clicked_Delete(Listbox), width=20)
    DeleteButton.grid(row=4, column=1, padx=5, pady= 5)

    Add_Game_Frame = Tk.LabelFrame(Main_GUI, text='Add Game')
    Add_Game_Frame.grid(columnspan=3, row=1,  padx=(20, 20), pady=(5, 10))

    EnterGameLabeL = Tk.ttk.Label(Add_Game_Frame, text='Enter Game Name')
    EnterGameLabeL.grid(row=0, column=0)

    GameNameEntry = Tk.ttk.Entry(Add_Game_Frame, width=70, exportselection=0)
    GameNameEntry.grid(row=0, column=1, columnspan=2, pady=10, padx=5)

    EnterSaveLabeL = Tk.ttk.Label(Add_Game_Frame, text='Enter Save Location')
    EnterSaveLabeL.grid(row=1, column=0)

    GameSaveEntry = Tk.ttk.Entry(Add_Game_Frame, width=70, exportselection=0)
    GameSaveEntry.grid(row=1, column=1, columnspan=2, pady=5, padx=5)

    ConfirmButton = Tk.ttk.Button(Add_Game_Frame, text='Confirm',
        command=lambda: App.Add_Game_Pressed(GameNameEntry, GameSaveEntry, Listbox), width=20)
    ConfirmButton.grid(row=2, column=0, padx=5, pady= 5)

    BrowseButton = Tk.ttk.Button(Add_Game_Frame, text='Browse',
        command=lambda: App.Browse_Click(GameNameEntry, GameSaveEntry), width=20)
    BrowseButton.grid(row=2, column=1, padx=5, pady= 5)

    ClearButton = Tk.ttk.Button(Add_Game_Frame, text='Clear', command=App.Add_Game_Pressed, width=20)
    ClearButton.grid(row=2, column=2, padx=5, pady= 5)

    App.Database_Check()

    Main_GUI.mainloop()
    game_list.close()

if __name__ == '__main__':
    main()
