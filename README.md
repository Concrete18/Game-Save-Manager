# Game Save Manager

Tkinter Interface for running through an SQLite Database that allows backing up game saves easily.

![Image of Game Save Manager](https://github.com/Concrete18/Game-Save-Manager/blob/master/images/Screenshot.png)

Made in Python 3.8.3

## Features

* Up to 4 backup redundancy to prevent corruption issues.
* Easily add, delete and update games in the backup database using the interface.
* Selecting games shows useful info such as number of saves, size they all take combined and time since last backup.
* Fully works with python built in modules only.
* Smart Browse will use a game name to search for the best starting point for selecting the games save location.

## Python Techniques Used

* Tkinter messagebox and directory dialog
* SQLite Database
* File copying and other manipulations
* Object oriented design
* Full Logging System for most all actions and errors

## Config

```json
{
    "settings": {
        "backup_dest": "Save Backup",
        "backup_redundancy": 3,
        "disable_resize": 1,
        "center_window": 1
    },
    "extra_save_directories":[
        "D:/My Documents"
    ]
}
```

## Todo

* Total Games and Total size only updates on program restart.
* Change location that the current save is backed up to before restoring to current backup location.

## Bugs

* Renaming twice in a row brings up an error.
* leaving the file dialog open prevents closing interface.
* Wrong error messagebox if you clear the entry boxes and then click add game.
