from utils.config import get_env_variable
from dataclasses import dataclass, field
import json
import os

@dataclass
class GroqConfig:
    token: str = field(init=False)
    model1: str = field(init=False)
    model2: str = field(init=False)
    backup_model: str = field(init=False)

    def __post_init__(self):
        get_env_variable()
        self.token = os.getenv('GROQ_TOKEN')
        if not self.token:
            raise EnvironmentError("GROQ_TOKEN environment variable is not set.")

        try:
            with open('../config/config.json', 'r') as f:
                config_file = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise FileNotFoundError(f"Error loading config file: {e}")

        self.model1 = config_file.get('model1')
        self.model2 = config_file.get('model2')
        self.backup_model = config_file.get('backup_model')

        if not self.model1 or not self.backup_model:
            raise ValueError("Model configurations are missing in config.json.")