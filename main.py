import datetime as dt
import pandas as pd
import shutil
import os

def main():
    # backup_storage = 'D:\Google Drive\Games\Game Saves'
    backup_storage = f'{os.getcwd()}\\Testing Area\\Save Backup'
    game_list = pd.read_csv('Game_info.csv')

    # print(game_list.columns)
    # print(game_list.sort_index(axis=0, level='Last Backup', ascending=True))
    # for game in os.listdir(TargetDir):

    def Delete_Oldest(game):
        saves_list = []
        for file in os.listdir(f'{backup_storage}\\{game}'):
            saves_list.append(file)
        if len(saves_list) < 4:
            print('3 or Less Saves.')
            return
        else:
            print('More then 3 Saves.')
            saves_list.sort(reverse=True)
            print(saves_list)

    def Save_Backup(game_name):
        current_time = dt.datetime.now().strftime("%d-%m-%y %H-%M")
        dest = f'{backup_storage}\\{game_name}\\{current_time}'
        test_save_loc = 'D:\My Documents\My Games\Hacknet\Accounts'
        try:
            shutil.copytree(test_save_loc, dest)
        except FileExistsError:
            print('Save Already Backed up.')
        Delete_Oldest(game_name)

    # delete_oldest('Hacknet')
    Save_Backup('Hacknet')

if __name__ == '__main__':
    main()
