import configparser

DEFAULT_CONFIG = {"Overlay": {"additional_text": "", "additional_text_enabled": False}}


class Config:
    def read_config(self, path):
        self.path = path
        self.config = configparser.ConfigParser()
        if not self.config.read(path):
            self.config.read_dict(DEFAULT_CONFIG)
            self.write_config()

    def write_config(self):
        with open(self.path, "w") as configfile:
            self.config.write(configfile)

    def get_additional_text(self):
        return self.config["Overlay"]["additional_text"]

    def get_additional_text_enabled(self):
        return self.config["Overlay"].getboolean("additional_text_enabled")


config = Config()
