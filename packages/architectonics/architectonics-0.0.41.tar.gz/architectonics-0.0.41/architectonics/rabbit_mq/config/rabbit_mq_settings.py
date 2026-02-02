import os

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class BaseRabbitMQSettings(BaseModel):
    RABBITMQ_USER: str = os.getenv("RABBITMQ_USER")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD")
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST")
    RABBITMQ_PORT: int = int(os.getenv("RABBITMQ_PORT"))
    RABBITMQ_VHOST: str = os.getenv("RABBITMQ_VHOST")
