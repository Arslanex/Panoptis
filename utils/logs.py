from datetime import datetime
import logging
import os


class Logger:
    def __init__(self, log_dir="../logs/", log_level=logging.DEBUG, console_level=logging.ERROR):
        self.log_dir = log_dir
        self.log_level = log_level
        self.console_level = console_level
        self.log_format = '%(asctime)s - %(levelname)s - %(message)s'

        self._setup_log_directory()
        self.logger = self._configure_logger()

    def _setup_log_directory(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _get_log_filename(self):
        date_str = datetime.now().strftime('%Y-%m-%d')
        return os.path.join(self.log_dir, f'{date_str}.log')

    def _get_log_formatter(self):
        return logging.Formatter(self.log_format)

    def _configure_logger(self):
        logger = logging.getLogger("Panoptis")
        logger.setLevel(self.log_level)

        if not logger.hasHandlers():
            log_filename = self._get_log_filename()
            file_handler = logging.FileHandler(log_filename)
            file_handler.setLevel(self.log_level)
            file_handler.setFormatter(self._get_log_formatter())
            logger.addHandler(file_handler)

            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.console_level)
            console_handler.setFormatter(self._get_log_formatter())
            logger.addHandler(console_handler)

        return logger

    def get_logger(self):
        return self.logger