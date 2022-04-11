from pydantic import BaseModel, Extra
from configs.config import Config as TConfig

class Config(BaseModel, extra=Extra.ignore):
    tencent_secret_id: str = TConfig.get_config("mockingbird","TENCENT_SECRET_ID")
    tencent_secret_key: str = TConfig.get_config("mockingbird","TENCENT_SECRET_KEY")
    tts_project_id: str = ""
