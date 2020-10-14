from logging.handlers import RotatingFileHandler
from Backup_Class import Backup
from tkinter import ttk
import datetime as dt
import tkinter as Tk
import logging as lg
import threading
import sqlite3
import time
import os


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

    main_gui = Tk.Tk()
    main_gui.title('Game Save Manager')
    main_gui.iconbitmap('Save_Icon.ico')
    # window_width = 600
    # window_height = 477
    # width = int((main_gui.winfo_screenwidth()-window_width)/2)
    # height = int((main_gui.winfo_screenheight()-window_height)/2)
    # main_gui.geometry(f'{window_width}x{window_height}+{width}+{height}')

    # FIXME Binds do not work.
    main_gui.bind_class("Button", "<Key-Return>", lambda event: event.widget.invoke())
    main_gui.unbind_class("Button", "<Key-space>")

    # Main Row 0
    Backup_Frame = Tk.Frame(main_gui)
    Backup_Frame.grid(columnspan=4, column=0, row=0,  padx=(20, 20), pady=(5, 10))

    info_text = f'Total Games in Database: {len(App.Game_list_Sorted())}\nSize of Backups: {App.Convert_Size()}'
    Title = Tk.Label(Backup_Frame, text=info_text, font=(BoldBaseFont, 10))
    Title.grid(columnspan=4, row=0, column=1)

    BackupButton = ttk.Button(Backup_Frame, text='Backup Selected Game Save',
        command=lambda: App.Save_Backup(game_listbox.get(Tk.ACTIVE), ActionInfo), width=20)
    BackupButton.grid(row=3, column=1, padx=5)

    RestoreGameButton = ttk.Button(Backup_Frame, text='Restore Selected Game',
        command=lambda: App.Restore_Backup(), width=20)
    RestoreGameButton.grid(row=3, column=2, padx=5)

    DeleteButton = ttk.Button(Backup_Frame, text='Delete Selected Game',
        command=lambda: App.Delete_Game_from_DB(game_listbox), width=20)
    DeleteButton.grid(row=3, column=3, padx=5)

    # Main Row 1
    instruction = 'Select a Game'
    ActionInfo = Tk.Label(main_gui, text=instruction, font=(BoldBaseFont, 10))
    ActionInfo.grid(columnspan=4, row=1, column=0, padx=5, pady= 5)

    # Main Row 2
    ListboxFrame = Tk.Frame(main_gui)
    ListboxFrame.grid(columnspan=4, row=2, column=0,  padx=(20, 20), pady=(5, 10))

    scrollbar = Tk.Scrollbar(ListboxFrame, orient=Tk.VERTICAL)
    scrollbar.config(command=Tk.Listbox.yview)
    scrollbar.grid(row=0, column=2, sticky='ns', rowspan=3)

    game_listbox = Tk.Listbox(ListboxFrame, exportselection=False, yscrollcommand=scrollbar.set, font=(BoldBaseFont, 12), height=10, width=60)
    game_listbox.bind('<<ListboxSelect>>', lambda event, game_listbox=game_listbox,:
        App.Delete_Update_Entry(game_listbox, GameSaveEntry, GameNameEntry, 1))
    game_listbox.grid(columnspan=2, row=0, column=0)

    sorted_list = App.Game_list_Sorted()
    for item in sorted_list:
        game_listbox.insert(Tk.END, item)

    # Main Row 3
    Add_Game_Frame = Tk.LabelFrame(main_gui, text='Add/Update Game')
    Add_Game_Frame.grid(columnspan=4, row=3,  padx=15, pady=(5, 17))

    EnterGameLabeL = Tk.ttk.Label(Add_Game_Frame, text='Enter Game Name')
    EnterGameLabeL.grid(row=0, column=0)

    entry_width = 65
    GameNameEntry = Tk.ttk.Entry(Add_Game_Frame, width=entry_width, exportselection=0)
    GameNameEntry.grid(row=0, column=1, columnspan=3, pady=8, padx=5)

    EnterSaveLabeL = Tk.ttk.Label(Add_Game_Frame, text='Enter Save Location')
    EnterSaveLabeL.grid(row=1, column=0)

    GameSaveEntry = Tk.ttk.Entry(Add_Game_Frame, width=entry_width, exportselection=0)
    GameSaveEntry.grid(row=1, column=1, columnspan=3, pady=5)

    # Button Frame Row 2
    Button_Frame = Tk.Frame(Add_Game_Frame)
    Button_Frame.grid(columnspan=4, row=2)

    button_padx = 4
    button_pady = 5
    ConfirmAddButton = Tk.ttk.Button(Button_Frame, text='Add Entered Game',
        command=lambda: App.Add_Game_Pressed(GameNameEntry, GameSaveEntry, game_listbox), width=20)
    ConfirmAddButton.grid(row=2, column=0, padx=button_padx, pady=button_pady)

    UpdateButton = Tk.ttk.Button(Button_Frame, text='Update Selected Game',
        command=lambda: App.Update_Game(GameNameEntry, GameSaveEntry, game_listbox), width=20)
    UpdateButton.grid(row=2, column=1, padx=button_padx, pady=button_pady)

    BrowseButton = Tk.ttk.Button(Button_Frame, text='Browse for Save',
        command=lambda: App.Browse_For_Save(GameNameEntry, GameSaveEntry), width=20)
    BrowseButton.grid(row=2, column=2, padx=button_padx, pady=button_pady)

    ClearButton = Tk.ttk.Button(Button_Frame, text='Clear Entries',
        command=lambda: App.Delete_Update_Entry(game_listbox, GameNameEntry, GameSaveEntry), width=20)
    ClearButton.grid(row=2, column=3, padx=button_padx, pady=button_pady)

    App.Database_Check()

    main_gui.mainloop()

    game_list.close()

if __name__ == '__main__':
    main()
