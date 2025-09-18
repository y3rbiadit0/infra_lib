import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class CredentialsProvider:
    access_key_id: str
    secret_access_key: str
    url: str
    region: str

    @classmethod
    def from_env(cls, root_dir: Path) -> "CredentialsProvider":
        return cls(
            access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            url=os.getenv("AWS_ENDPOINT_URL"),
            region=os.getenv("AWS_DEFAULT_REGION"),
        )
