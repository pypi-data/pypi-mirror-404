from e80.lib.context import E80ContextObject
import yaml

from pydantic import BaseModel, Field
from pathlib import Path


class AuthInfo(BaseModel):
    auth_token: str


class UserConfig(BaseModel):
    auth_info: dict[str, AuthInfo] = Field(default_factory=dict)
    api_url: str = "https://app.8080.io"


def get_auth_info(ctx_obj: E80ContextObject) -> AuthInfo | None:
    user_config = read_user_config()
    if user_config is None:
        return None

    auth = user_config.auth_info.get(ctx_obj.platform_host)
    if auth is None:
        return None

    return auth


def read_user_config() -> UserConfig | None:
    config = Path.home() / ".8080" / "user.yaml"

    if not config.exists():
        return None

    with config.open() as f:
        yaml_dict = yaml.safe_load(f)
        if not yaml_dict:
            return None
        parsed = UserConfig.model_validate(yaml_dict)
        return parsed


def write_user_config(config: UserConfig):
    config_dir = Path.home() / ".8080"

    if not config_dir.exists():
        config_dir.mkdir(parents=True, exist_ok=True)

    file = config_dir / "user.yaml"

    with file.open(mode="w") as f:
        model_dict = config.model_dump()
        model_str = yaml.dump(model_dict)
        f.write(model_str)
