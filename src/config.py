import os
from typing import Dict, Any, List
import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class CsvConfig(BaseModel):
    column_map: Dict[str, str] = {"name": "name", "website": "website", "email": "email"}

class ScrapeConfig(BaseModel):
    concurrency: int = 4
    timeout_ms: int = 20000
    max_pages: int = 3
    max_text_chars: int = 20000
    politeness_delay_ms: int = 1000
    respect_robots: bool = True

class AnalysisConfig(BaseModel):
    pagespeed_strategy: str = "mobile"
    thresholds: Dict[str, int] = {"perf": 50, "seo": 70, "load_ms": 4000}
    broken_link_sample: int = 10

class ServiceMapConfig(BaseModel):
    max_findings: int = 3

class LlmConfig(BaseModel):
    default_model: str = "claude-sonnet-4-6"
    default_provider: str = "anthropic"
    temperature: float = 0.4
    max_generation_attempts: int = 3

class EmailConfig(BaseModel):
    cta: str = "reply to this email"
    sender_name: str = ""
    sender_company: str = ""
    physical_address: str = ""
    unsubscribe_base_url: str = ""
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    temperature: float = 0.4

class SendConfig(BaseModel):
    provider: str = "gmail"
    daily_send_limit: int = 30
    per_message_delay_s: float = 20.0
    dry_run: bool = True
    require_human_review: bool = True

class ApiConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: List[str] = ["http://localhost:5173"]
    auth_token_required: bool = True

class JobsConfig(BaseModel):
    backend: str = "inprocess"
    max_concurrent_jobs: int = 1

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    # Config sections from config.yaml
    csv: CsvConfig = CsvConfig()
    scrape: ScrapeConfig = ScrapeConfig()
    analysis: AnalysisConfig = AnalysisConfig()
    service_map: ServiceMapConfig = ServiceMapConfig()
    llm: LlmConfig = LlmConfig()
    email: EmailConfig = EmailConfig()
    send: SendConfig = SendConfig()
    api: ApiConfig = ApiConfig()
    jobs: JobsConfig = JobsConfig()

    # Secret keys loaded from OS environment or .env
    anthropic_api_key: str = Field(default="", validation_alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    google_api_key: str = Field(default="", validation_alias="GOOGLE_API_KEY")
    pagespeed_api_key: str = Field(default="", validation_alias="PAGESPEED_API_KEY")
    gmail_oauth_credentials: str = Field(default="./secrets/gmail_oauth.json", validation_alias="GMAIL_OAUTH_CREDENTIALS")
    gmail_token_path: str = Field(default="./secrets/gmail_token.json", validation_alias="GMAIL_TOKEN_PATH")
    api_auth_token: str = Field(default="", validation_alias="API_AUTH_TOKEN")

    @classmethod
    def load_settings(cls, config_path: str = "config.yaml") -> "Settings":
        yaml_data = {}
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f) or {}
        return cls(**yaml_data)

settings = Settings.load_settings()
