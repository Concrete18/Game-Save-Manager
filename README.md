# Game Save Manager

Tkinter Interface for running through an SQLite Database that allows backing up game saves easily.

![Image of Game Save Manager](https://raw.githubusercontent.com/Concrete18/Game-Save-Manager/master/images/Screenshot.png)

Made in Python 3.8.3

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
* Fully works with python built in modules only
* SQLite Database
* File copying and other manipulations
* Object oriented design
* Full Logging System for most all actions and errors

## Config

```json
{
    "settings":{
        "backup_dest":"Save Backup",
        "backup_redundancy":3,
        "enable_compression":1,
        "compression_type":"zip",
        "disable_resize":1,
        "center_window":1,
        "text_output":0,
        "debug":1
    },
    "custom_save_directories":[
        "D:/My Documents",
        "D:/My Installed Games/Steam Games/steamapps/common"
    ]
}
```

## Todo

* Total Games and Total size only updates on program restart.
* Arrow Key listbox navigation

## Bugs

* leaving the file dialog open prevents closing interface.
* Game backup size shows as 0 after finishing a backup until it is clicked again.
