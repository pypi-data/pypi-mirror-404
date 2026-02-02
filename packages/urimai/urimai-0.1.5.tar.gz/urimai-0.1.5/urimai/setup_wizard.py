"""Rich-powered first-run setup wizard for urimai."""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from urimai.config import (
    DEFAULT_CONFIG,
    save_config,
    store_api_key,
    get_api_key,
    ensure_data_dir,
    CONFIG_FILE,
    URIMAI_HOME,
)

console = Console()


def run_setup_wizard() -> None:
    """Interactive setup wizard that collects config and API keys."""
    console.print()
    console.print(
        Panel(
            "[bold cyan]Welcome to urimai![/bold cyan]\n\n"
            "This wizard will help you configure the AI-powered SQL answer engine.\n"
            "Your settings will be saved to [green]~/.urimai/config.toml[/green].\n"
            "API keys are stored securely in your system keyring.",
            border_style="bold blue",
            padding=(1, 2),
        )
    )
    console.print()

    ensure_data_dir()

    config = DEFAULT_CONFIG.copy()
    config["user"] = dict(config["user"])
    config["provider"] = dict(config["provider"])
    config["settings"] = dict(config["settings"])

    # 1. User name
    name = Prompt.ask("[bold]Your name[/bold]", default="")
    config["user"]["name"] = name

    # 2. Default provider
    provider = Prompt.ask(
        "[bold]Default AI provider[/bold]",
        choices=["google", "openai"],
        default="google",
    )
    config["provider"]["default"] = provider

    # 3. API key for chosen provider
    _prompt_api_key(provider)

    # 4. Model name
    if provider == "google":
        model = Prompt.ask(
            "[bold]Google model name[/bold]",
            default=config["provider"]["google_model"],
        )
        config["provider"]["google_model"] = model
    else:
        model = Prompt.ask(
            "[bold]OpenAI model name[/bold]",
            default=config["provider"]["openai_model"],
        )
        config["provider"]["openai_model"] = model

    # 5. Optional: configure the other provider
    other = "openai" if provider == "google" else "google"
    if Confirm.ask(f"\n[bold]Configure {other} too?[/bold]", default=False):
        _prompt_api_key(other)
        if other == "google":
            m = Prompt.ask(
                "[bold]Google model name[/bold]",
                default=config["provider"]["google_model"],
            )
            config["provider"]["google_model"] = m
        else:
            m = Prompt.ask(
                "[bold]OpenAI model name[/bold]",
                default=config["provider"]["openai_model"],
            )
            config["provider"]["openai_model"] = m

    # 6. Review
    console.print()
    table = Table(title="Configuration Summary", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Name", config["user"]["name"] or "(not set)")
    table.add_row("Default provider", config["provider"]["default"])
    table.add_row("Google model", config["provider"]["google_model"])
    table.add_row("OpenAI model", config["provider"]["openai_model"])
    table.add_row("Google API key", _mask_key(get_api_key("google")))
    table.add_row("OpenAI API key", _mask_key(get_api_key("openai")))
    table.add_row("Config file", str(CONFIG_FILE))
    table.add_row("Data directory", str(URIMAI_HOME))

    console.print(table)
    console.print()

    if not Confirm.ask("[bold]Save this configuration?[/bold]", default=True):
        console.print("[yellow]Setup cancelled.[/yellow]")
        return

    # 7. Save
    save_config(config)
    console.print()
    console.print("[green]Configuration saved![/green]")
    console.print(f"[dim]Config file: {CONFIG_FILE}[/dim]")
    console.print()
    console.print("[bold]Get started:[/bold]")
    console.print("  urim init <path>    Register a database or CSV file")
    console.print("  urim config         View current settings")
    console.print()


def _prompt_api_key(provider: str) -> None:
    """Prompt for and store an API key if not already set."""
    existing = get_api_key(provider)
    if existing:
        console.print(f"[dim]{provider} API key already configured ({_mask_key(existing)})[/dim]")
        if not Confirm.ask(f"Replace existing {provider} API key?", default=False):
            return

    key = Prompt.ask(f"[bold]{provider.capitalize()} API key[/bold]", password=True)
    if key.strip():
        store_api_key(provider, key.strip())
        console.print(f"[green]{provider.capitalize()} API key stored securely[/green]")
    else:
        console.print(f"[yellow]No key entered for {provider}[/yellow]")


def _mask_key(key: str) -> str:
    """Mask an API key for display (show first 4 and last 4 chars)."""
    if not key:
        return "(not set)"
    if len(key) <= 12:
        return key[:4] + "..." + key[-2:]
    return key[:4] + "..." + key[-4:]
