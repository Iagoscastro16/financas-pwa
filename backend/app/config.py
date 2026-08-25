import os

from dotenv import load_dotenv

load_dotenv()

AUTH_USERNAME = os.environ["AUTH_USERNAME"]
AUTH_PASSWORD_HASH = os.environ["AUTH_PASSWORD_HASH"]
JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 dias
