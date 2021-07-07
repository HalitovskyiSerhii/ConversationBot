from pydantic import Field, BaseSettings


class Settings(BaseSettings):
    storage_url: str = Field(..., env='storage_url')
    storage_access_key: str = Field(..., env='storage_access_key')
    storage_secret_key: str = Field(..., env='storage_secret_key')
    storage_files_bucket: str = Field(..., env='storage_files_bucket')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


cfg = Settings()
