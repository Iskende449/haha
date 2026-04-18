from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    APP_NAME: str = 'Nomad Heritage API'
    DEBUG: bool = False
    LOG_LEVEL: str = 'INFO'

    DB_HOST: str = 'localhost'
    DB_PORT: int = 5432
    DB_USER: str = 'hakaton'
    DB_PASSWORD: str = 'hakaton_secret'
    DB_NAME: str = 'hakaton_db'

    JWT_SECRET_KEY: str = 'please-change-me'
    JWT_ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    ORS_API_KEY: str = ''
    ORS_TIMEOUT: int = 15
    MAPBOX_ACCESS_TOKEN: str = ''
    MAPBOX_TIMEOUT: int = 15
    OSRM_BASE_URL: str = 'https://router.project-osrm.org'
    OSRM_TIMEOUT: int = 15

    GEMINI_API_KEY: str = ''
    GEMINI_MODEL: str = 'gemini-1.5-flash'

    CHECKIN_RADIUS_METERS: int = 100
    CHECKIN_XP_REWARD: int = 50

    @property
    def async_database_url(self) -> str:
        return (
            f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}'
            f'@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f'postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}'
            f'@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
        )


settings = Settings()
