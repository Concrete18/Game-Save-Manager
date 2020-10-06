import configparser


class Backup(self):
    Config = configparser.ConfigParser()
    Config.read('Config.ini')
    self.backup_dest = Config.get('Main', 'backup_dest')
    self.backup_redundancy = int(Config.get('Main', 'backup_redundancy'))

