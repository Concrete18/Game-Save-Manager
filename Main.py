from functools import partial
import datetime as dt
import tkinter as Tk
import pandas as pd
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


    def Add_Game_to_DB():
        c = game_list.cursor()
        game_name = input('What is the game name?')
        save_location = input('What is the game name?')
        c.execute("INSERT INTO games VALUES (:game_name, :save_location, :last_backup)",
        {'game_name': game_name, 'save_location': save_location, 'last_backup': dt.datetime.now()})
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
        c.execute("SELECT game_name FROM games ORDER BY last_backup")
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
        var = dt.datetime.now()
        c.execute("""UPDATE games SET last_backup = :last_backup WHERE game_name = :game_name""",
        {'game_name': game, 'last_backup': var})
        Delete_Oldest(game)


    # Defaults for Background and fonts
    Background = 'White'
    BoldBaseFont = "Arial Bold"
    BaseFont = "Arial"

    Main_GUI = Tk.Tk()
    Main_GUI.title('Game Save Manager')
    # Main_GUI.iconbitmap('Power.ico')
    Main_GUI.configure(bg=Background)
    # Main_GUI.resizable(width=False, height=False)

    Title_Frame = Tk.Frame(Main_GUI, bg=Background)
    Title_Frame.grid(columnspan=4, padx=(20, 20), pady=(5, 10))

    Title = Tk.Label(Title_Frame, text='Game Save Manager', font=(BoldBaseFont, 20), bg=Background)
    Title.grid(column=0, row=0)

    def Clicked_Backup():
        Save_Backup(clicked.get())

    clicked = Tk.StringVar(Main_GUI)
    sorted_list = Game_list_Sorted()
    clicked.set(sorted_list[0]) # set the default option

    popupMenu = Tk.OptionMenu(Main_GUI, clicked, *sorted_list)
    popupMenu.grid(row=2, column=1)
    popupMenu["menu"].config(bg=Background)

    BackupButton = Tk.Button(text='Backup', command=partial(Clicked_Backup))
    BackupButton.grid(row=2, column=2)

    Main_GUI.mainloop()
    game_list.close()


if __name__ == '__main__':
    main()