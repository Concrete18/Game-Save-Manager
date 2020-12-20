# Game Save Manager

Tkinter Interface for running through an SQLite Database that allows backing up game saves easily.

![Image of Game Save Manager](https://raw.githubusercontent.com/Concrete18/Game-Save-Manager/master/Screenshot.png)

Made in Python 3.8.3

## Features

* Up to 4 backup redundancy to prevent corruption issues.
* Easily add, delete and update games in the backup database using the interface.
* Selecting games shows useful info such as number of saves, size they all take combined and time since last backup.
* Fully works with python built in modules only.

## Python Techniques Used

* Tkinter messagebox and directory dialog
* SQLite Database
* File copying and other manipulations
* Object oriented design
* Full Logging System for most all actions and errors

## Known Bugs

* Bindings do not properly disable space acting as enter key.
