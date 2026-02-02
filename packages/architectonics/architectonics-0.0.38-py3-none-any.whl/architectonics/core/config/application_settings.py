import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class ApplicationSettings(BaseModel):
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"


application_settings = ApplicationSettings()
