"""
Configuration management using Pydantic Settings
"""
from typing import List, Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # DNSE API Configuration
    dnse_api_base_url: str = Field(default="https://api.dnse.com.vn")
    dnse_api_key: str = Field(default="")
    dnse_api_secret: str = Field(default="")
    dnse_account_id: str = Field(default="")

    # MQTT Configuration
    mqtt_broker: str = Field(default="mqtt.dnse.com.vn")
    mqtt_port: int = Field(default=1883)
    mqtt_username: str = Field(default="")
    mqtt_password: str = Field(default="")
    mqtt_client_id: str = Field(default="dnse_trading_bot")

    # Trading Configuration
    trading_mode: Literal["paper", "live"] = Field(default="paper")
    max_position_size: float = Field(default=100_000_000)  # VND
    max_positions: int = Field(default=10)
    risk_per_trade: float = Field(default=0.02)
    default_stop_loss_pct: float = Field(default=0.03)

    # DCA Bot Configuration
    dca_enabled: bool = Field(default=False)
    dca_interval_hours: int = Field(default=24)
    dca_amount_per_order: float = Field(default=10_000_000)  # VND
    dca_symbols: str = Field(default="VCB,VHM,VIC")

    @property
    def dca_symbols_list(self) -> List[str]:
        """Parse DCA symbols as list"""
        return [s.strip() for s in self.dca_symbols.split(",") if s.strip()]

    # Telegram Notifications
    telegram_bot_token: str = Field(default="")
    telegram_chat_id: str = Field(default="")
    telegram_enabled: bool = Field(default=True)

    # Redis Configuration
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)

    # Database Configuration
    database_url: str = Field(default="sqlite:///./dnse_trading.db")

    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/trading_bot.log")

    # Strategy Configuration
    enable_breakout_strategy: bool = Field(default=True)
    enable_support_resistance_strategy: bool = Field(default=True)
    enable_volatility_cutloss: bool = Field(default=True)

    # Risk Management
    max_drawdown_pct: float = Field(default=0.10)
    volatility_threshold: float = Field(default=0.05)


# Global settings instance
settings = Settings()
