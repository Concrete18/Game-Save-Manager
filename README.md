# Game Save Manager

Tkinter Interface for running through an SQLite Database that allows backing up game saves easily.

![Image of Game Save Manager](https://raw.githubusercontent.com/Concrete18/Game-Save-Manager/master/images/Screenshot.png)

Made with Python 3.8.3

## Features

### Backup and Restore

- Up to 4 backup redundancy to prevent corruption issues.
- Easily add, delete and update games in the backup database using the interface.
- Selecting games shows useful info such as number of saves, size they all take combined and time since last backup.

### Smart Browse

- Smart Browse will use a game name to search for the best starting point for selecting the games save location.
- Some games do not include the name in the save directory path so they can't be found.

Written in Rust unlike the rest of the code.

### Game Search

![Image of Smart Browse](https://raw.githubusercontent.com/Concrete18/Game-Save-Manager/master/images/Search%20Example.png)

- Full game database search above game list.
- Instant search results as you type without having to hit enter.

### Backup Compression

- Backup of saves uses compression for saving space.
- Use below command to view available compression formats.

```python
shutil.get_archive_formats()
```

### Misc

- Detects any games with no longer existing save paths. (Allows listing only missing games for removing/updating)

## Python Techniques Used

- Tkinter messagebox and directory dialog
- SQLite Database
- File copying and other manipulations
- Object oriented design
- Full Logging System for most all actions and errors
- Rust Code used as a Python Package via Maturin for speeding up the save search

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

## Setup

### Setup Steps with Explanations

- Install [Rust](https://www.rust-lang.org/) on your system if you do not already have it
- Create Python Virtual Environment using `python -m venv .env`
- Activate the env using `.env\Scripts\activate`
- Run `pip install -r requirements.txt`
- Run `maturin develop` in order to create the rust package within the environment (Info on how I did this was found in this [Maturin Tutorial](https://www.youtube.com/watch?v=DpUlfWP_gtg&t=1s))
- Run the Save manager with the `run_game_save_manager.vbs` file. You can make a shortcut out of it to make running it easier. (This is required due to the python virtual environment)

### Commands Only

```bash
python -m venv .env
.env\Scripts\activate
pip install -r requirements.txt
maturin develop
```

<!-- ## Todo

- Arrow Key listbox navigation -->

## Testing

Use this to run all tests. Currently only works on my computer when testing smart browse due to the
game save folders existing on it.

```cmd
python -m unittest
```

## Bugs

- Backing up the same game multiple times during the same selection causes duplication of the selected game in the
  listbox.
- Renaming multiples times in one session causes issues.
- leaving the file dialog open prevents closing interface.
- Game backup size shows as 0 after finishing a backup until it is clicked again.
