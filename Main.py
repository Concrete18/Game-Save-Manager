from tkinter import messagebox
import datetime as dt
import tkinter as Tk
import sqlite3
import shutil
import os

def main():
    game_list = sqlite3.connect('game_list.db')
    c = game_list.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS games (
    game_name text,
    save_location text,
    last_backup text
    )''')
    backup_redundancy = 3 # Total previous backups to keep after each backup is made.
    backup_storage = 'Testing Area\\Save Backup'


    def Add_Game_to_DB(game_name, save_location):
        c = game_list.cursor()
        c.execute("INSERT INTO games VALUES (:game_name, :save_location, :last_backup)",
        {'game_name': game_name, 'save_location': save_location, 'last_backup': dt.datetime.now()})
        game_list.commit()


    def Delete_Game_from_DB(game_name):
        c = game_list.cursor()
        c.execute("DELETE FROM games WHERE game_name = :game_name", {'game_name': game_name})
        game_list.commit()


    def get_save_loc(game):
        print(f'Getting Save location for {game}.')
        game_list = sqlite3.connect('game_list.db')
        c = game_list.cursor()
        c.execute("SELECT save_location FROM games WHERE game_name=:game_name", {'game_name': game})
        save_location = c.fetchone()[0]
        return save_location


    def Game_list_Sorted():
        c = game_list.cursor()
        c.execute("SELECT game_name FROM games ORDER BY last_backup DESC")
        ordered_games = []
        for game_name in c.fetchall():
            ordered_games.append(game_name[0])
        game_list.commit()
        return ordered_games


    def Delete_Oldest(game):
        saves_list = []
        dir = os.path.join(backup_storage, game)
        print(dir)
        for file in os.listdir(dir):
            file = os.path.join(dir, file)
            saves_list.append(file)
        if len(saves_list) < 4:
            print('3 or Less Saves.')
            return
        else:
            print('More then 3 Saves.')
            sorted_list = sorted(saves_list, key=os.path.getctime, reverse=True)
            for i in range(backup_redundancy, len(saves_list)):
                shutil.rmtree(sorted_list[i])

    def Save_Backup(game):
        current_time = dt.datetime.now().strftime("%d-%m-%y %H-%M")
        dest = os.path.join(backup_storage, game, current_time)
        save_loc = get_save_loc(game)
        try:
            shutil.copytree(save_loc, dest)
        except FileNotFoundError:
            print('No Action Completed - File location does not exist.')
        except FileExistsError:
            print('No Action Completed - Save Already Backed up.')
        c = game_list.cursor()
        c.execute("""UPDATE games SET last_backup = :last_backup WHERE game_name = :game_name""",
        {'game_name': game, 'last_backup': dt.datetime.now()})
        game_list.commit()
        Delete_Oldest(game)


    # Defaults for Background and fonts
    Background = 'White'
    BoldBaseFont = "Arial Bold"
    BaseFont = "Arial"

    Main_GUI = Tk.Tk()
    Main_GUI.title('Game Save Manager')
    Main_GUI.iconbitmap('Save_Icon.ico')
    Main_GUI.configure()
    Main_GUI.resizable(width=False, height=False)
    Main_GUI.bind_class("Button", "<Key-Return>", lambda event: event.widget.invoke())
    Main_GUI.unbind_class("Button", "<Key-space>")


    Backup_Frame = Tk.Frame(Main_GUI)
    Backup_Frame.grid(columnspan=4, row=0,  padx=(20, 20), pady=(5, 10))

    # Title = Tk.Label(Backup_Frame, text='Game Save Manager', font=(BoldBaseFont, 20))
    # Title.grid(column=0, row=0)

    Guide = Tk.Label(Backup_Frame, text='Select the game that you want to backup.\n Ordered by last backup in dropdown.', font=(BaseFont, 10))
    Guide.grid(columnspan=4, row=1)


    def Clicked_Backup():
        Save_Backup(clicked.get())


    def Clicked_Delete():
        Delete_Check = messagebox.askyesno(title='Game Save Manager', message='Are you sure that you want to delete the game?')
        if Delete_Check:
          Delete_Game_from_DB(clicked.get())


    clicked = Tk.StringVar(Main_GUI)
    sorted_list = Game_list_Sorted()
    clicked.set(sorted_list[0]) # set the default option

    popupMenu = Tk.OptionMenu(Backup_Frame, clicked, *sorted_list)
    popupMenu.grid(row=2, columnspan=4, pady=10)

    BackupButton = Tk.Button(Backup_Frame, text='Backup Game Save', command=Clicked_Backup)
    BackupButton.grid(row=3, column=1, padx=5)

    DeleteButton = Tk.Button(Backup_Frame, text='Delete Game From Database', command=Clicked_Delete)
    DeleteButton.grid(row=3, column=2, padx=5)

    Add_Game_Frame = Tk.Frame(Main_GUI)
    Add_Game_Frame.grid(columnspan=4,row=1, padx=(20, 20), pady=(5, 10))


    def Add_Game_Pressed():
        game_name = GameNameEntry.get()
        save_location = GameSaveEntry.get()
        GameSaveEntry.delete(0, Tk.END)
        GameNameEntry.delete(0, Tk.END)
        Add_Game_to_DB(game_name, save_location)


    def On_Click(event):
        event.widget.delete(0, Tk.END)


    EnterGameLabeL = Tk.Label(Add_Game_Frame, text='Enter Game Name')
    EnterGameLabeL.grid(row=0, column=0)

    GameNameEntry = Tk.Entry(Add_Game_Frame, width=50, exportselection=0)
    GameNameEntry.grid(row=0, column=1, pady=5, padx=5)
    GameNameEntry.bind("<Button-1>", On_Click)

    EnterSaveLabeL = Tk.Label(Add_Game_Frame, text='Enter Save Location')
    EnterSaveLabeL.grid(row=1, column=0)

    GameSaveEntry = Tk.Entry(Add_Game_Frame, width=50, exportselection=0)
    GameSaveEntry.grid(row=1, column=1, pady=5, padx=5)
    GameSaveEntry.bind("<Button-1>", On_Click)

    AddGame = Tk.Button(Add_Game_Frame, text='Add Game to Database', command=Add_Game_Pressed)
    AddGame.grid(row=3, columnspan=4)

    Delete_Game_Frame = Tk.Frame(Main_GUI)
    Delete_Game_Frame.grid(columnspan=4,row=2, padx=(20, 20), pady=(5, 10))

    Main_GUI.mainloop()
    game_list.close()


if __name__ == '__main__':
    main()