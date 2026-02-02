"""
Command line tool that generates shell commands based on user input prompts and optionally executes them.
"""

import os
import platform
import re
import subprocess
import sys

from pydantic_ai.agent import Agent
from pydantic_ai.models import Model
from yaspin import yaspin

from shai_python.config import (
    GREEN,
    RED,
    RESET,
    YELLOW,
    ConfigManager,
    ModelConfig,
    ProviderConfig,
    ShellCommand,
)
from shai_python.strings import _

risk_color = {
    "safe": GREEN,
    "caution": YELLOW,
    "danger": RED,
}


def format_danger_level(danger_level: str) -> str:
    """Format danger level with color"""
    color = risk_color.get(danger_level.lower(), RESET)
    return f"{color}{danger_level.upper()}{RESET}"


def get_windows_shell_type():
    try:
        import psutil
        current_process = psutil.Process(os.getpid())
        for _ in range(5):
            parent = current_process.parent()
            if not parent:
                break
            parent_name = parent.name().lower()
            if "python" in parent_name or "uv" in parent_name:
                current_process = parent
                continue
            if "pwsh" in parent_name or "powershell" in parent_name:
                return "PowerShell"
            if "cmd" in parent_name:
                return "Windows CMD"
            if "bash" in parent_name or "zsh" in parent_name:
                return parent_name
            current_process = parent
        return "Generic/Unknown"
    except Exception:
        return "Unknown"


def get_system_info():
    """Get system environment information"""
    system = platform.system()  # Linux, Darwin (macOS), Windows
    release = platform.release()
    shell = os.environ.get("SHELL")
    if "windows" == system.lower():
        shell = get_windows_shell_type()

    return f"""
Operating System: {system}
System Version: {release}
Shell: {shell}
"""


def execute_shell_command(command: str):
    """Execute shell command"""
    # Safety check: prevent some dangerous operations
    dangerous_patterns = [
        r"rm\s+-rf\s+/",  # Delete root directory
        r"rm\s+-rf\s+\$HOME",  # Delete home directory
        r"rm\s+-rf\s+\*",  # Delete all content in current directory
        r">\s*/dev/sda",  # Direct write to disk device
        r"dd\s+if=",  # Disk write command
        r":\(\)\{\s*:|\s*&\s*\};",  # Fork bomb
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, command):
            print(_("dangerous_pattern_detected", command=command))
            confirm = input(_("confirm_dangerous_command"))
            if confirm != "YES":
                print(_("dangerous_command_cancelled"))
                return

    try:
         # Linux/Mac or Windows CMD
        process_cmd = command
        if platform.system() == "Windows" and get_windows_shell_type() == "PowerShell":
            process_cmd = ["powershell", "-Command", command]

        subprocess.run(
            process_cmd,
            shell=True,
            check=True,
            text=True,
        )

    except subprocess.CalledProcessError as e:
        print(_("command_execution_failed", exit_code=e.returncode))


def display_shell_command(shell_cmd: ShellCommand):
    """Show shell command with color"""
    # Get color for command based on danger level
    command_color = risk_color.get(shell_cmd.risk.lower(), RESET)

    print(f"\ncmd>> {command_color}{shell_cmd.command}{RESET}")
    print(f"{shell_cmd.explanation}\n")

    # Decide whether to execute command based on danger level
    if shell_cmd.risk.lower() == "danger":
        response = (
            input(_("risk_level_prompt", risk_level=format_danger_level(shell_cmd.risk)))
            .strip()
            .lower()
        )
        if response != "yes":
            print(_("command_not_executed"))
            return
    else:
        response = input(_("execute_prompt", risk_level=format_danger_level(shell_cmd.risk))).strip().lower()

    if response in ["y", "yes"]:
        execute_shell_command(shell_cmd.command)
    else:
        print(_("command_not_executed"))


def create_model(model_entry: ModelConfig, provider_info: ProviderConfig) -> Model:
    """Create model based on provider"""
    if model_entry.provider == "deepseek":
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.deepseek import DeepSeekProvider
        model = OpenAIChatModel(model_name=model_entry.id, provider=DeepSeekProvider(api_key=provider_info.api_key))
    elif model_entry.provider == "google":
        from pydantic_ai.models.google import GoogleModel
        from pydantic_ai.providers.google import GoogleProvider
        model = GoogleModel(model_name=model_entry.id, provider=GoogleProvider(api_key=provider_info.api_key))
    elif model_entry.provider == "anthropic":
        from pydantic_ai.models.anthropic import AnthropicModel
        from pydantic_ai.providers.anthropic import AnthropicProvider
        model = AnthropicModel(model_name=model_entry.id, provider=AnthropicProvider(api_key=provider_info.api_key))
    elif model_entry.provider == "xai":
        from pydantic_ai.models.xai import XaiModel
        from pydantic_ai.providers.xai import XaiProvider
        model = XaiModel(model_name=model_entry.id, provider=XaiProvider(api_key=provider_info.api_key))
    elif model_entry.provider == "openrouter":
        from pydantic_ai.models.openrouter import OpenRouterModel
        from pydantic_ai.providers.openrouter import OpenRouterProvider
        model = OpenRouterModel(model_name=model_entry.id, provider=OpenRouterProvider(api_key=provider_info.api_key))
    else:
        from pydantic_ai.models.openai import OpenAIChatModel
        from pydantic_ai.providers.openai import OpenAIProvider
        provider = OpenAIProvider(
            base_url=provider_info.base_url,
            api_key=provider_info.api_key
        )
        model = OpenAIChatModel(model_name=model_entry.id, provider=provider)
    return model

def main():
    """Main function"""
    system_info = get_system_info()

    is_init = ConfigManager.ensure_config()
    if is_init:
        edit_command = ConfigManager.get_edit_command()
        display_shell_command(edit_command)
        return

    # Get user prompt from command line arguments or interactive input
    user_prompt = " ".join(sys.argv[1:])
    while not user_prompt:
        user_prompt = input(">> ").strip()

    if user_prompt.lower() in ("config", "configure", "cfg", "confg", "comfig"):
        edit_command = ConfigManager.get_edit_command()
        display_shell_command(edit_command)
        return

    try:
        config = ConfigManager.load_and_validate()

        target_name = config.default_model
        model_entry = next((m for m in config.models if m.id == target_name or m.alias == target_name), None)
        if not model_entry:
            raise ValueError(_("model_not_found", model_name=target_name))

        provider_info = config.providers.get(model_entry.provider)
        if not provider_info:
            raise ValueError(_("provider_not_configured", provider_name=model_entry.provider))

        if provider_info.api_key.startswith("$"):
            raise ValueError(_("env_var_not_defined", var_name=provider_info.api_key))

        model = create_model(model_entry, provider_info)

         # Create Agent
        agent = Agent(
            model=model,
            output_type=ShellCommand,
            system_prompt=(
                f"You are a professional shell command generation assistant. Based on the user's description, generate accurate shell commands."
                f"Also provide brief command explanations and evaluate the risk level."
                f"Risk levels ('safe', harmless commands), 'caution' (may have side effects), or 'danger' (potentially harmful)."
                f"Ensure commands are compatible with the current system environment.\n\n"
                f"Current system environment information:\n{system_info}"
            ),
        )

    except Exception as e:
        print(f"{RED}{_('config_init_error', error=e)}{RESET}")
        edit_command = ConfigManager.get_edit_command()
        display_shell_command(edit_command)
        return

    with yaspin(text=_("thinking"), color="yellow") as spinner:
        try:
            result = agent.run_sync(user_prompt)
        except Exception as e:
            spinner.fail(_("erorr", error=e))
            exit(1)

    display_shell_command(result.output)

if __name__ == "__main__":
    main()
