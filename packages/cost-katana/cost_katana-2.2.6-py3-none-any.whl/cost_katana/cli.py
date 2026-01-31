"""
Command-line interface for Cost Katana
"""

import argparse
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

try:
    from . import configure, create_generative_model, CostKatanaClient
    from .config import Config
    from .exceptions import CostKatanaError
except ImportError:
    # Handle case when running as script
    from cost_katana.config import Config
    from cost_katana.exceptions import CostKatanaError

console = Console()


def create_sample_config():
    """Create a sample configuration file"""
    sample_config = {
        "api_key": "dak_your_api_key_here",
        "base_url": "https://api.costkatana.com",
        "default_model": "gemini-2.0-flash",
        "default_temperature": 0.7,
        "default_max_tokens": 2000,
        "cost_limit_per_day": 50.0,
        "enable_analytics": True,
        "enable_optimization": True,
        "enable_failover": True,
        "model_mappings": {
            "gemini": "gemini-2.0-flash-exp",
            "claude": "anthropic.claude-3-sonnet-20240229-v1:0",
            "gpt4": "gpt-4-turbo-preview",
        },
        "providers": {
            "google": {"priority": 1, "models": ["gemini-2.0-flash", "gemini-pro"]},
            "anthropic": {
                "priority": 2,
                "models": ["claude-3-sonnet", "claude-3-haiku"],
            },
            "openai": {"priority": 3, "models": ["gpt-4", "gpt-3.5-turbo"]},
        },
    }
    return sample_config


def init_config(args):
    """Initialize configuration"""
    config_path = Path(args.config or "cost_katana_config.json")

    if config_path.exists() and not args.force:
        console.print(
            f"[yellow]Configuration file already exists: {config_path}[/yellow]"
        )
        if not Confirm.ask("Overwrite existing configuration?"):
            return

    console.print("[bold blue]Setting up Cost Katana configuration...[/bold blue]")

    # Get API key
    api_key = Prompt.ask(
        "Enter your Cost Katana API key", default=args.api_key if args.api_key else None
    )

    # Get base URL
    base_url = Prompt.ask("Enter base URL", default="https://api.costkatana.com")

    # Get default model
    default_model = Prompt.ask(
        "Enter default model",
        default="gemini-2.0-flash",
        choices=["gemini-2.0-flash", "claude-3-sonnet", "gpt-4", "nova-pro"],
    )

    # Create configuration
    config_data = create_sample_config()
    config_data.update(
        {"api_key": api_key, "base_url": base_url, "default_model": default_model}
    )

    # Save configuration
    try:
        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=2)

        console.print(f"[green]Configuration saved to: {config_path}[/green]")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Test the configuration: [cyan]cost-katana test[/cyan]")
        console.print("2. Start a chat session: [cyan]cost-katana chat[/cyan]")
        console.print("3. See available models: [cyan]cost-katana models[/cyan]")

    except Exception as e:
        console.print(f"[red]Failed to save configuration: {e}[/red]")
        sys.exit(1)


def test_connection(args):
    """Test connection to Cost Katana API"""
    try:
        config_path = args.config or "cost_katana_config.json"

        if Path(config_path).exists():
            configure(config_file=config_path)
        elif args.api_key:
            configure(api_key=args.api_key)
        else:
            console.print(
                "[red]No configuration found. Run 'cost-katana init' first.[/red]"
            )
            return

        console.print("[bold blue]Testing Cost Katana connection...[/bold blue]")

        # Test with a simple model
        model = create_generative_model("gemini-2.0-flash")
        response = model.generate_content(
            "Hello! Please respond with just 'OK' to test the connection."
        )

        console.print(
            Panel(
                f"[green]✓ Connection successful![/green]\n"
                f"Model: {response.usage_metadata.model}\n"
                f"Response: {response.text}\n"
                f"Cost: ${response.usage_metadata.cost:.4f}\n"
                f"Latency: {response.usage_metadata.latency:.2f}s",
                title="Test Results",
            )
        )

    except Exception as e:
        console.print(f"[red]✗ Connection failed: {e}[/red]")
        sys.exit(1)


def list_models(args):
    """List available models"""
    try:
        config_path = args.config or "cost_katana_config.json"

        if Path(config_path).exists():
            configure(config_file=config_path)
        elif args.api_key:
            configure(api_key=args.api_key)
        else:
            console.print(
                "[red]No configuration found. Run 'cost-katana init' first.[/red]"
            )
            return

        client = CostKatanaClient(
            config_file=config_path if Path(config_path).exists() else None
        )
        models = client.get_available_models()

        table = Table(title="Available Models")
        table.add_column("Model ID", style="cyan", no_wrap=True)
        table.add_column("Display Name", style="magenta")
        table.add_column("Provider", style="green")
        table.add_column("Type", style="yellow")

        for model in models:
            model_id = model.get("id", model.get("modelId", "Unknown"))
            name = model.get("name", model.get("displayName", model_id))
            provider = model.get("provider", "Unknown")
            model_type = model.get("type", "Text")

            table.add_row(model_id, name, provider, model_type)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Failed to fetch models: {e}[/red]")
        sys.exit(1)


def start_chat(args):
    """Start an interactive chat session"""
    try:
        config_path = args.config or "cost_katana_config.json"

        if Path(config_path).exists():
            configure(config_file=config_path)
            config = Config.from_file(config_path)
        elif args.api_key:
            configure(api_key=args.api_key)
            config = Config(api_key=args.api_key)
        else:
            console.print(
                "[red]No configuration found. Run 'cost-katana init' first.[/red]"
            )
            return

        model_name = args.model or config.default_model

        console.print(
            Panel(
                f"[bold blue]Cost Katana Chat Session[/bold blue]\n"
                f"Model: {model_name}\n"
                f"Type 'quit' to exit, 'clear' to clear history",
                title="Welcome",
            )
        )

        model = create_generative_model(model_name)
        chat = model.start_chat()

        total_cost = 0.0

        while True:
            try:
                message = Prompt.ask("[bold cyan]You[/bold cyan]")

                if message.lower() in ["quit", "exit", "q"]:
                    break
                elif message.lower() == "clear":
                    chat.clear_history()
                    console.print("[yellow]Chat history cleared.[/yellow]")
                    continue
                elif message.lower() == "cost":
                    console.print(
                        f"[green]Total session cost: ${total_cost:.4f}[/green]"
                    )
                    continue

                console.print("[bold green]Assistant[/bold green]: ", end="")

                with console.status("Thinking..."):
                    response = chat.send_message(message)

                console.print(response.text)

                # Show cost info
                total_cost += response.usage_metadata.cost
                console.print(
                    f"[dim]Cost: ${response.usage_metadata.cost:.4f} | "
                    f"Total: ${total_cost:.4f} | "
                    f"Tokens: {response.usage_metadata.total_tokens}[/dim]\n"
                )

            except KeyboardInterrupt:
                console.print("\n[yellow]Chat session interrupted.[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                continue

        console.print(f"\n[bold]Session Summary:[/bold]")
        console.print(f"Total Cost: ${total_cost:.4f}")
        console.print("Thanks for using Cost Katana!")

    except Exception as e:
        console.print(f"[red]Failed to start chat: {e}[/red]")
        sys.exit(1)


def get_prompt_from_args_or_file(args):
    """Get prompt from command line argument or file"""
    if hasattr(args, "prompt") and args.prompt:
        return args.prompt

    if hasattr(args, "file") and args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            console.print(f"[red]Error: File '{args.file}' not found[/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Error reading file: {e}[/red]")
            sys.exit(1)

    # Interactive input
    return Prompt.ask("Enter prompt to process")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Cost Katana - Unified AI interface with cost optimization"
    )
    parser.add_argument(
        "--config",
        "-c",
        help="Configuration file path (default: cost_katana_config.json)",
    )
    parser.add_argument("--api-key", "-k", help="Cost Katana API key")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize configuration")
    init_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing config"
    )

    # Test command
    subparsers.add_parser("test", help="Test API connection")

    # Models command
    subparsers.add_parser("models", help="List available models")

    # Chat command
    chat_parser = subparsers.add_parser("chat", help="Start interactive chat")
    chat_parser.add_argument("--model", "-m", help="Model to use for chat")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Route to appropriate function
    if args.command == "init":
        init_config(args)
    elif args.command == "test":
        test_connection(args)
    elif args.command == "models":
        list_models(args)
    elif args.command == "chat":
        start_chat(args)


if __name__ == "__main__":
    main()
