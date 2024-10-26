import time
import json
import os
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple, Dict, Any

from slack_client import SlackClient
from analysis import MessageAnalyser
from dataclass import GroqConfig
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm

# Constants
LAST_ACTION_FILE = 'last_action.json'
LOG_FILE = 'bot.log'

# Setup console for rich output
console = Console()

def configure_logging() -> logging.Logger:
    """Configure logging settings."""
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = configure_logging()

def save_last_action_time() -> None:
    """Save the current timestamp to the last_action.json file."""
    now = datetime.now()
    try:
        with open(LAST_ACTION_FILE, 'w') as f:
            json.dump({'last_action': now.isoformat()}, f, indent=4)
    except IOError as e:
        logger.error(f"Error saving last action time: {e}")

def load_last_action_time() -> Optional[datetime]:
    """Load the last action timestamp from the last_action.json file."""
    if not os.path.exists(LAST_ACTION_FILE):
        return None
    try:
        with open(LAST_ACTION_FILE, 'r') as f:
            data = json.load(f)
            return datetime.fromisoformat(data['last_action'])
    except (IOError, ValueError, KeyError) as e:
        logger.error(f"Error loading last action time: {e}")
        return None

def list_channels(client: SlackClient) -> List[str]:
    """Fetch and display available Slack channels, allowing multi-selection."""
    try:
        channels = client.fetch_channels().get('data', [])
        if not channels:
            console.print("[bold red]No channels available![/bold red]")
            return []

        table = Table(title="Available Slack Channels")
        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Name", style="magenta")

        for channel in channels:
            table.add_row(channel['id'], channel['name'])

        console.print(table)
        channel_ids = Prompt.ask(
            "[bold green]Enter the channel IDs to analyze (comma-separated)[/bold green]"
        )

        selected_ids = [id_.strip() for id_ in channel_ids.split(',') if id_.strip()]
        valid_ids = {ch['id'] for ch in channels}

        invalid_ids = [id_ for id_ in selected_ids if id_ not in valid_ids]
        if invalid_ids:
            console.print(f"[bold red]Invalid channel IDs: {', '.join(invalid_ids)}[/bold red]")
            return []

        return selected_ids

    except Exception as e:
        logger.error(f"Error fetching channels: {e}")
        console.print(f"[bold red]Error fetching channels: {e}[/bold red]")
        return []

def select_action() -> str:
    """Display the action menu and return the selected action."""
    console.print("[bold yellow]Select an operation:[/bold yellow]")
    console.print("1. Batch Analysis")
    console.print("2. Toxicity Analysis")
    console.print("3. Both (Batch + Toxicity)")

    choice = IntPrompt.ask("Enter your choice", choices=["1", "2", "3"])
    return ["batch", "toxicity", "both"][choice - 1]

def select_time_range() -> Tuple[datetime, datetime]:
    """Provide the user with time range options and return the selected range."""
    last_action_time = load_last_action_time()
    options = [
        "Last 2 hours", "Last 5 hours", "Last 12 hours",
        "Today (midnight to now)",
        "From Last Action to Now" if last_action_time else "(No Last Action Available)",
        "Custom time range"
    ]

    for idx, option in enumerate(options, 1):
        console.print(f"{idx}. {option}")

    choice = IntPrompt.ask("Enter your choice", choices=[str(i) for i in range(1, 7)])
    end_time = datetime.now()

    if choice == 1:
        start_time = end_time - timedelta(hours=2)
    elif choice == 2:
        start_time = end_time - timedelta(hours=5)
    elif choice == 3:
        start_time = end_time - timedelta(hours=12)
    elif choice == 4:
        start_time = datetime(end_time.year, end_time.month, end_time.day)
    elif choice == 5 and last_action_time:
        start_time = last_action_time
    else:
        start_time = _prompt_for_custom_time("start")
        end_time = _prompt_for_custom_time("end")

    console.print(f"[bold green]Selected Time Range:[/bold green] {start_time} to {end_time}")
    return start_time, end_time

def _prompt_for_custom_time(label: str) -> datetime:
    """Prompt user to enter a custom time."""
    while True:
        try:
            time_str = Prompt.ask(f"Enter the {label} time (YYYY-MM-DD HH:MM)")
            return datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        except ValueError:
            console.print("[bold red]Invalid time format. Please try again.[/bold red]")

def filter_messages_by_time(
    messages: List[Dict[str, Any]], start_time: datetime, end_time: datetime
) -> List[Dict[str, Any]]:
    """Filter messages based on the selected time range."""
    return [
        msg for msg in messages
        if 'ts' in msg and start_time <= datetime.fromtimestamp(float(msg['ts'])) <= end_time
    ]

def perform_analysis_on_multiple_channels(
    client: SlackClient, analyser: MessageAnalyser, channel_ids: List[str], action: str,
    start_time: datetime, end_time: datetime
) -> None:
    """Perform the selected analysis on multiple channels in parallel."""

    def analyze_channel(channel_id: str) -> None:
        perform_analysis(client, analyser, channel_id, action, start_time, end_time)

    with ThreadPoolExecutor() as executor:
        executor.map(analyze_channel, channel_ids)

def perform_analysis(
    client: SlackClient, analyser: MessageAnalyser, channel_id: str, action: str,
    start_time: datetime, end_time: datetime
) -> None:
    """Fetch messages, filter by time, and perform the selected analysis."""
    try:
        messages = client.fetch_channel_messages(channel_id).get('data', [])
        messages = filter_messages_by_time(messages, start_time, end_time)

        if not messages:
            console.print("[bold red]No messages found in the selected time range![/bold red]")
            return

        _execute_analysis(analyser, messages, action)
        save_last_action_time()
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        console.print(f"[bold red]Analysis failed: {e}[/bold red]")

def _execute_analysis(analyser: MessageAnalyser, messages: List[Dict[str, Any]], action: str) -> None:
    """Execute the appropriate analysis based on user choice."""
    if action in ["batch", "both"]:
        response = analyser.perform_batch_analysis(messages)
        _display_analysis_result(response, "Batch Analysis")

    if action in ["toxicity", "both"]:
        response = analyser.perform_multiple_toxicity_analysis(messages)
        _display_toxicity_results(response)

def _display_analysis_result(response: Dict[str, Any], analysis_type: str) -> None:
    """Display the result of an analysis."""
    if response.get('success'):
        console.print(f"[bold green]{analysis_type} Result:[/bold green]")
        console.print(response.get('data')[0])
    else:
        console.print(f"[bold red]{analysis_type} Failed: {response.get('error')}[/bold red]")

def _display_toxicity_results(response: Dict[str, Any]) -> None:
    """Display toxicity analysis results."""
    if response.get('success'):
        table = Table(title="Toxicity Analysis Results")
        table.add_column("Text", style="magenta")
        table.add_column("Result", justify="center", style="cyan")

        for item in response.get('data', []):
            table.add_row(item['text'], item['result'])

        console.print(table)
    else:
        console.print(f"[bold red]Toxicity Analysis Failed: {response.get('error')}[/bold red]")

def main() -> None:
    """Main entry point for the CLI."""
    client = SlackClient()
    analyser = MessageAnalyser(GroqConfig())

    try:
        while True:
            channel_ids = list_channels(client)
            if not channel_ids:
                break

            action = select_action()
            start_time, end_time = select_time_range()
            perform_analysis_on_multiple_channels(client, analyser, channel_ids, action, start_time, end_time)

            if not Confirm.ask("[bold yellow]Analyze more channels?[/bold yellow]"):
                console.print("[bold green]Goodbye![/bold green]")
                break
    except KeyboardInterrupt:
        console.print("\n[bold red]Operation cancelled by user.[/bold red]")

if __name__ == '__main__':
    main()
