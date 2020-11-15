from logging.handlers import RotatingFileHandler
from Backup_Class import Backup
from tkinter import messagebox
from tkinter import ttk
import tkinter as Tk
import logging as lg
import sqlite3
import os


def main():
    # logger info and setup
    log_formatter = lg.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%m-%d-%Y %I:%M:%S %p')
    logger = lg.getLogger(__name__)
    logger.setLevel(lg.DEBUG)
    my_handler = RotatingFileHandler('Game_Backup.log', maxBytes=5*1024*1024, backupCount=2)
    my_handler.setFormatter(log_formatter)
    logger.addHandler(my_handler)

    # database creation
    game_list = sqlite3.connect('game_list.db')
    App = Backup(game_list, logger)
    App.cursor.execute('''
    CREATE TABLE IF NOT EXISTS games (
    game_name text,
    save_location text,
    last_backup text
    )''')

    # Settings Check
    if not os.path.exists(App.backup_dest):
        messagebox.showwarning(title='Game Save Manager', message='Backup destination does not exist.')

    # Defaults
    BoldBaseFont = "Arial Bold"

    main_gui = Tk.Tk()
    main_gui.title('Game Save Manager')
    main_gui.iconbitmap('Save_Icon.ico')
    if App.disable_resize:  # sets window to not resize if disable_resize is set to 1
        main_gui.resizable(width=False, height=False)
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
    Backup_Frame.grid(columnspan=4, column=0, row=0,  padx=(20, 20), pady=(5, 0))

    info_text = f'Total Games in Database: {len(App.Game_list_Sorted())}\nSize of Backups: {App.Convert_Size(App.backup_dest)}'
    Title = Tk.Label(Backup_Frame, text=info_text, font=(BoldBaseFont, 10))
    Title.grid(columnspan=4, row=0, column=1)

    button_width = 26
    BackupButton = ttk.Button(Backup_Frame, text='Backup Selected Game Save',
        command=lambda: App.Save_Backup(game_listbox.get(Tk.ACTIVE), ActionInfo, game_listbox), width=button_width)
    BackupButton.grid(row=3, column=1, padx=5, pady=5)

    RestoreGameButton = ttk.Button(Backup_Frame, text='Restore Selected Game Save',
        command=App.Restore_Backup, width=button_width)
    RestoreGameButton.grid(row=3, column=2, padx=5)

    ExploreSaveButton = ttk.Button(Backup_Frame, text='Explore Selected Game Save',
        command=App.Explore_Save_location, width=button_width)
    ExploreSaveButton.grid(row=3, column=3, padx=5)

    # Main Row 1
    instruction = 'Select a Game\nto continue'
    ActionInfo = Tk.Label(main_gui, text=instruction, font=(BoldBaseFont, 10))
    ActionInfo.grid(columnspan=4, row=1, column=0, padx=5, pady= 3)

    # Main Row 2
    ListboxFrame = Tk.Frame(main_gui)
    ListboxFrame.grid(columnspan=4, row=2, column=0,  padx=(20, 20), pady=(5, 10))

    scrollbar = Tk.Scrollbar(ListboxFrame, orient=Tk.VERTICAL)
    scrollbar.grid(row=0, column=3, sticky='ns', rowspan=3)

    game_listbox = Tk.Listbox(ListboxFrame, exportselection=False,
        yscrollcommand=scrollbar.set, font=(BoldBaseFont, 12), height=10, width=60)
    game_listbox.bind('<<ListboxSelect>>', lambda event, game_listbox=game_listbox,:
        App.Delete_Update_Entry(game_listbox, GameSaveEntry, GameNameEntry, ActionInfo, 1))
    game_listbox.grid(columnspan=3, row=0, column=0)
    scrollbar.config(command=game_listbox.yview)

    sorted_list = App.Game_list_Sorted()
    for item in sorted_list:
        game_listbox.insert(Tk.END, item)

    # Main Row 3
    Add_Game_Frame = Tk.LabelFrame(main_gui, text='Manage Games')
    Add_Game_Frame.grid(columnspan=4, row=3,  padx=15, pady=(5, 17))

    EnterGameLabeL = Tk.ttk.Label(Add_Game_Frame, text='Enter Game Name')
    EnterGameLabeL.grid(row=0, column=0)

    entry_width = 65
    GameNameEntry = Tk.ttk.Entry(Add_Game_Frame, width=entry_width, exportselection=0)
    GameNameEntry.grid(row=0, column=1, columnspan=3, pady=8, padx=5)

    EnterSaveLabeL = Tk.ttk.Label(Add_Game_Frame, text='Enter Save Location')
    EnterSaveLabeL.grid(row=1, column=0)

    GameSaveEntry = Tk.ttk.Entry(Add_Game_Frame, width=entry_width, exportselection=0)
    GameSaveEntry.grid(row=1, column=1, columnspan=3, pady=5, padx=10)

    BrowseButton = Tk.ttk.Button(Add_Game_Frame, text='Browse',
        command=lambda: App.Browse_For_Save(GameSaveEntry))
    BrowseButton.grid(row=1, column=4, padx=10)

    # Button Frame Row 2
    Button_Frame = Tk.Frame(Add_Game_Frame)
    Button_Frame.grid(columnspan=5, row=2, pady=(5, 5))

    button_padx = 4
    button_pady = 5
    ConfirmAddButton = Tk.ttk.Button(Button_Frame, text='Add Game',
        command=lambda: App.Add_Game_Pressed(GameNameEntry, GameSaveEntry, game_listbox), width=20)
    ConfirmAddButton.grid(row=2, column=0, padx=button_padx, pady=button_pady)

    UpdateButton = Tk.ttk.Button(Button_Frame, text='Update Game',
        command=lambda: App.Update_Game(GameNameEntry, GameSaveEntry, game_listbox), width=20)
    UpdateButton.grid(row=2, column=1, padx=button_padx, pady=button_pady)

    RemoveButton = ttk.Button(Button_Frame, text='Remove Game',
        command=lambda: App.Delete_Game_from_DB(game_listbox, GameNameEntry, GameSaveEntry, info_text), width=20)
    RemoveButton.grid(row=2, column=2, padx=button_padx, pady=button_pady)

    ClearButton = Tk.ttk.Button(Button_Frame, text='Clear Entries',
        command=lambda: App.Delete_Update_Entry(game_listbox, GameNameEntry, GameSaveEntry, info_text), width=20)
    ClearButton.grid(row=2, column=3, padx=button_padx, pady=button_pady)

    App.Database_Check()

    main_gui.mainloop()

    game_list.close()

if __name__ == '__main__':
    main()
