from typing import Optional
from dotenv import dotenv_values


def dotenv_to_db(driver: str, env_path: Optional[str] = None) -> dict:
    env = dotenv_values(env_path)
    return dict(
        ENGINE=driver,
        NAME=env['DB_NAME'],
        USER=env['DB_USER'],
        PASSWORD=env['DB_PASSWORD'],
        HOST=env['DB_HOST'],
        PORT=env['DB_PORT']
    )
