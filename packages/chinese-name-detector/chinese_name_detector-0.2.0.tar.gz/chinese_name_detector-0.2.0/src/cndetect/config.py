from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path

class ExcelConfig(BaseModel):
    paths: List[str] = []
    column: str = "Name"
    output_suffix: str = "_cn"
    output_dir: Optional[str] = None

class MatchingConfig(BaseModel):
    mode: str = "overall"  # overall, component, strict

class LogConfig(BaseModel):
    level: str = "INFO"
    file: Optional[str] = None
    rotation: str = "1 MB"
    retention: str = "7 days"
    redact_names: bool = True

class Settings(BaseSettings):
    family_name_path: Optional[str] = None
    custom_family_names: List[str] = []
    exclude_family_names: List[str] = []
    excel: ExcelConfig = ExcelConfig()
    matching: MatchingConfig = MatchingConfig()
    log: LogConfig = LogConfig()

    model_config = SettingsConfigDict(
        env_prefix="CNSCAN_",
        env_nested_delimiter="__",
        extra="ignore"
    )

    @classmethod
    def load_settings(cls, config_path: Optional[str] = None) -> "Settings":
        # 优先级: CLI > Env > YAML > Default
        # Pydantic Settings 处理了 Env 和 Default
        # 我们这里简单实现 YAML 加载逻辑，如果指定了 config_path
        if config_path and os.path.exists(config_path):
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return cls(**data)
        
        # 默认查找顺序
        search_paths = [
            Path("cndetect.yaml"),
            Path.home() / ".config" / "cndetect" / "config.yaml"
        ]
        for p in search_paths:
            if p.exists():
                import yaml
                with open(p, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    return cls(**data)
                    
        return cls()

settings = Settings.load_settings()
