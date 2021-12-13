import configparser


class Config:


    def __init__(self, config_path):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)


    def set_redundancy(self, redundancy):
        '''
        ph
        '''
        if redundancy.isnumeric():
            redundancy = int(redundancy) 
        else:
            redundancy = 3
        if not 0 < redundancy < 4:
            redundancy = 3
        return redundancy

    def get_settings(self):
        # settings
        self.backup_dest = self.config['SETTINGS']['backup_dest']
        self.compression_type = self.config['SETTINGS']['compression_type']
        self.backup_redundancy = self.set_redundancy(self.config['SETTINGS']['backup_redundancy'])
        self.quick_backup = self.config['SETTINGS'].getboolean('quick_backup')
        self.center_window = self.config['SETTINGS'].getboolean('center_window')
        self.disable_resize = self.config['SETTINGS'].getboolean('disable_resize')
        # debug
        self.output = self.config['DEBUG'].getboolean('text_output')
        self.debug = self.config['DEBUG'].getboolean('enable_debug')
        # custom save directories
        self.custom_dirs = [dir for name, dir in self.config['CUSTOM_SAVE_DIRECTORIES'].items()]


if __name__ == '__main__':
    cfg = Config('config\settings.ini')
    cfg.get_settings()
    print(cfg.backup_redundancy)
    # print(config.compression_type)
    # print(config.backup_redundancy)
    # print(config.quick_backup)
    # print(config.center_window)
    # print(config.disable_resize)
