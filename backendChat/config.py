import os
import pytz
from dotenv import load_dotenv

load_dotenv(".env")

load_dotenv(".env.local", override=True)

# Configs
timezone = pytz.timezone(os.getenv("TIMEZONE", "Europe/London"))

PROJECTS_LOCATION = os.getenv("PROJECTS_LOCATION", "projects")
QUESTIONNAIRES_LOCATION = os.getenv("QUESTIONNAIRES_LOCATION", "questionnaires")

HOST_VOLUME_PATH = os.getenv("HOST_VOLUME_PATH", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

FLASK_RUN_HOST = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
FLASK_RUN_PORT = int(os.getenv("FLASK_RUN_PORT", 8080))
