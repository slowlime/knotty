from fastapi import FastAPI

from .config import load_config

config = load_config()
app = FastAPI()
