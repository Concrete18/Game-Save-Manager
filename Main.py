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
    script_root = os.getcwd()
    backup_redundancy = 3 # Total previous backups to keep after each backup is made.
    backup_storage = 'placeholder'
    testing_storage = os.path.join(os.getcwd(), 'Testing Area\\Save Backup')
    os.chdir(testing_storage)


    def Add_Game_to_DB():
        c = game_list.cursor()
        game_name = input('What is the game name?')
        save_location = input('What is the game name?')
        c.execute("INSERT INTO games VALUES (:game_name, :save_location, :last_backup)",
        {'game_name': game_name, 'save_location': save_location, 'last_backup': dt.datetime.now()})
        game_list.commit()


    def get_save_loc(game):
        print(game)
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
        dir = os.path.join(os.getcwd(), game)
        for file in os.listdir(dir):
            print(file)
            file = os.path.join(dir, file)
            saves_list.append(file)
        print(saves_list)
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
        dest = f'{os.getcwd()}\\{game}\\{current_time}'
        dest = os.path.join(os.getcwd(), game, current_time)
        save_loc = get_save_loc(game)
        try:
            shutil.copytree(save_loc, dest)
        except FileNotFoundError:
            print('No Action Completed - File location does not exist.')
        except FileExistsError:
            print('No Action Completed - Save Already Backed up.')
        game_list.at[game, 'Last Backup'] = dt.datetime.now()
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

    # Create a Tkinter variable
    tkvar = Tk.StringVar(Main_GUI)
    sorted_list = Game_list_Sorted()

    popupMenu = Tk.OptionMenu(Main_GUI, tkvar, *sorted_list)
    popupMenu.grid(row=2, column=1)
    popupMenu["menu"].config(bg=Background)
    tkvar.set(sorted_list[0]) # set the default option
    # popupMenu.focus_set()

    # on change dropdown value
    def change_dropdown(*args):
        print( tkvar.get() )

    # link function to change dropdown
    tkvar.trace('w', change_dropdown)

    BackupButton = Tk.Button(text='Backup', command=partial(Save_Backup, tkvar.get()))
    BackupButton.grid(row=2, column=2)

    Main_GUI.mainloop()


if __name__ == '__main__':
    main()
    game_list.close()