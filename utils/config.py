from dotenv import load_dotenv
from pathlib import Path


def get_env_variable(path='../.env'):
    dotenv_path = Path(path)
    load_dotenv(dotenv_path=dotenv_path)
