import importlib.resources as pkg_resources
import os
import platform
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from shai_python.strings import _

# ANSI color codes for colored output
GREEN = "\033[92m"  # Green for safe
YELLOW = "\033[93m"  # Yellow for caution
RED = "\033[91m"  # Red for danger
RESET = "\033[0m"  # Reset color
BOLD = "\033[1m"  # Bold text


class ProviderConfig(BaseModel):
    api_key: str = Field(..., min_length=1, description="API key cannot be empty")
    base_url: str | None = None


class ModelConfig(BaseModel):
    id: str = Field(..., min_length=1, description="Model ID cannot be empty")
    provider: str = Field(..., min_length=1, description="Provider name cannot be empty")
    alias: str | None = None


class GlobalConfig(BaseModel):
    default_model: str = Field(..., min_length=1, description='effective model')
    providers: dict[str, ProviderConfig]
    models: list[ModelConfig]


class ShellCommand(BaseModel):
    """Shell command structure returned by the model"""
    command: str = Field(..., description="Generated shell command")
    explanation: str = Field(..., description="Command explanation")
    risk: str = Field(..., description="Risk levels ('safe', 'caution', 'danger')")


class ConfigManager:
    APP_NAME = "shai"
    # Use configuration directory in current working directory to avoid permission issues
    CONFIG_DIR = Path.home() / ".config" / APP_NAME
    CONFIG_FILE = CONFIG_DIR / "config.yaml"

    @classmethod
    def ensure_config(cls) -> bool:
        """Initialize configuration, copy from template if not exists"""
        if not cls.CONFIG_FILE.exists():
            cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            try:
                # Use importlib.resources to read template from package
                # Assume template is in shai_python package
                template_data = pkg_resources.read_text("shai_python", "config.template.yaml")
                with open(cls.CONFIG_FILE, "w", encoding="utf-8") as f:
                    f.write(template_data)
                return True  # Indicates first-time initialization
            except Exception as e:
                print(_("config_init_error", error=e))
        return False

    @classmethod
    def get_edit_command(cls) -> ShellCommand:
        """Get ShellCommand object for editing configuration"""
        system = platform.system()
        config_path = str(cls.CONFIG_FILE)

        if system == "Windows":
            cmd = f"notepad {config_path}"
        else:
            # Prefer environment variable $EDITOR, default to vim
            editor = os.environ.get("EDITOR", "vim")
            cmd = f"{editor} {config_path}"

        explanation = _(
            "config_edit_explanation",
            yellow_shai_config=f"{YELLOW}'shai config'{RESET}"
        )

        return ShellCommand(
            command=cmd,
            explanation=explanation,
            risk="safe"
        )

    @classmethod
    def load_and_validate(cls) -> GlobalConfig:
        """Load and validate configuration"""
        if not cls.CONFIG_FILE.exists():
            raise FileNotFoundError(_("config_file_missing"))

        with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
            # Simple environment variable substitution support (optional)
            content = f.read()
            # Match ${VAR} and replace
            content = re.sub(r"\${(\w+)}", lambda m: os.getenv(m.group(1), m.group(0)), content)

            data = yaml.safe_load(content)
            return GlobalConfig(**data)
