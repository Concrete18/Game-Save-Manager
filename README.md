# Game Save Manager

Tkinter Interface for running through an SQLite Database that allows backing up game saves easily.

![Image of Game Save Manager](https://raw.githubusercontent.com/Concrete18/Game-Save-Manager/master/images/Screenshot.png)

Made with Python 3.8.3

## Features

### Backup and Restore

* Up to 4 backup redundancy to prevent corruption issues.
* Easily add, delete and update games in the backup database using the interface.
* Selecting games shows useful info such as number of saves, size they all take combined and time since last backup.

### Smart Browse

![Image of Smart Browse](https://raw.githubusercontent.com/Concrete18/Game-Save-Manager/master/images/Smart%20Browse%20Progress.png)
![Image of Smart Browse](https://raw.githubusercontent.com/Concrete18/Game-Save-Manager/master/images/Smart%20Browse%20Complete.png)

* Smart Browse will use a game name to search for the best starting point for selecting the games save location.
* Progress bar showing progress for Smart Browse Search.
* Some games do not include the name in the save directory path so they can't be found.
* If Smart Browse is uses while the Save Entry has a path, a pop up will let you know if the search found a
different directory then what is currently entered.
* If a game save is entered when searching, you will be told if the found save is different from the current.

### Game Search

![Image of Smart Browse](https://raw.githubusercontent.com/Concrete18/Game-Save-Manager/master/images/Search%20Example.png)

* Full game database search above game list.
* Instant search results as you type without having to hit enter.

### Backup Compression

* Backup compression for saving space can be enabled in the config.
* When restoring, compressed files are detected regardless of compression setting.
* Use below command to view available compression formats.

```python
shutil.get_archive_formats()
```

### Misc

* Detects any games with no longer existing save paths. (Allows listing only missing games for removing/updating)

## Python Techniques Used

* Tkinter messagebox and directory dialog
* SQLite Database
* File copying and other manipulations
* Object oriented design
* Full Logging System for most all actions and errors

## Config

```ini
[SETTINGS]
# sets the folder name (within script dir) or full directory that you you backups to go to
backup_dest = Save Backup
# determines type of compression used. Must be supported by python shutil
compression_type = zip
# determines how many previous backups to keep as a redundancy
backup_redundancy = 3
# enables using the enter key to quickly backup the currently selected game
quick_backup = True
# centers the window when it is first created
center_window = True
# disables resizing the window
disable_resize = True

[DEBUG]
# these can easily be ignored
text_output = False
enable_debug = False

[CUSTOM_SAVE_DIRECTORIES]
# add any new folders with whatever name(no spaces) you want
d_drive_steam = D:/My Installed Games/Steam Games/steamapps/common
```

## Requirements

```pip
pip install -r requirements.txt
```

## Todo

* Arrow Key listbox navigation

## Testing

Use this to run all tests. Currently only works on my computer when testing smart browse due to the
game save folders existing on it.

```cmd
python -m unittest
```

## Bugs

* Backing up the same game multiple times during the same selection causes duplication of the selected game in the
listbox.
* Renaming multiples times in one session causes issues.
* leaving the file dialog open prevents closing interface.
* Game backup size shows as 0 after finishing a backup until it is clicked again.
