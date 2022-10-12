import configparser, os


class Config:


    def __init__(self, config_path):
        self.config = configparser.ConfigParser()
        self.config.read(config_path)
        self.config_path = config_path


    def make_ini(self):
        '''
        Makes the ini file with default settings.
        '''
        # base settings
        self.config['SETTINGS']['backup_dest'] = 'unset'
        self.config['SETTINGS']['compression_type'] = 'zip'
        self.config['SETTINGS']['backup_redundancy'] = '3'
        self.config['SETTINGS']['quick_backup'] = 'True'
        self.config['SETTINGS']['center_window'] = 'True'
        self.config['SETTINGS']['disable_resize'] = 'True'
        # debug
        self.config['SETTINGS']['text_output'] = 'False'
        self.config['SETTINGS']['enable_debug'] = 'False'
        # custom directories
        self.config['CUSTOM_SAVE_DIRECTORIES']['example'] = 'example/path'
        # writes to file
        with open(self.config_path, 'w') as ini:
            self.config.write(ini)

    def set_setting(self, section, key, value):
        '''
        Sets the a setting to `value` based on `section` and `key`.
        '''
        self.config[section][key] = value
        with open(self.config_path, 'w') as ini:
            self.config.write(ini)

    def set_redundancy(self, redundancy):
        '''
        Sets redundancyso it is always a valid value.
        '''
        if redundancy.isnumeric():
            redundancy = int(redundancy) 
        else:
            redundancy = 3
        if not 0 < redundancy < 4:
            redundancy = 3
        self.set_setting('SETTINGS', 'backup_redundancy', str(redundancy))
        return redundancy

    def get_settings(self):
        '''
        Gets the setting variables based on the ini.
        '''
        if not os.path.exists(self.config_path):
            self.make_ini()
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
    # testing
    print(cfg.backup_redundancy)
