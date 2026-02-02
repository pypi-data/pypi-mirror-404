import os
import logging
from typing import Optional

def get_env_var(name: str, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Environment variable {name} is not set.")
    return value

def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
