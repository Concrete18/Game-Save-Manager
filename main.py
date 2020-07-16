import datetime as dt
import pandas as pd
import shutil
import os

def main():
    game_list = pd.read_csv('Game_info.csv')

    # print(game_list.columns)
    # print(game_list.sort_index(axis=0, level='Last Backup', ascending=True))
    # for game in os.listdir(TargetDir):
    script_root = os.getcwd()
    backup_storage = 'placeholder'
    testing_storage = os.path.join(os.getcwd(), 'Testing Area\\Save Backup')
    os.chdir(testing_storage)


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
            for i in range(3, len(saves_list)):
                shutil.rmtree(sorted_list[i])

    def Save_Backup(game, save_loc):
        current_time = dt.datetime.now().strftime("%d-%m-%y %H-%M")
        dest = f'{os.getcwd()}\\{game}\\{current_time}'
        dest = os.path.join(os.getcwd(), game, current_time)
        save_loc = 'D:\My Documents\My Games\Hacknet\Accounts'
        try:
            shutil.copytree(save_loc, dest)
        except FileNotFoundError:
            print('File location does not exist.')
        except FileExistsError:
            print('Save Already Backed up.')
        Delete_Oldest(game)


    game_name, save_location = 'Hacknet', 'D:\My Documents\My Games\Hacknet\Accounts'
    Save_Backup(game_name, save_location)

if __name__ == '__main__':
    main()
