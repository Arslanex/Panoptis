import os
import sys
from utils.logger import CustomLogger
from datetime import datetime, timedelta
from src.slack_client import SlackClient
from src.groq_client import MessageAnalyser
from config import *

def convert_timestamp(ts):
    return datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M:%S')

def main():
    logger = CustomLogger().get_logger()

    try:
        logger.info('Initializing Slack client and message analyser')
        client = SlackClient(SLACK_BOT_TOKEN)
        analyser = MessageAnalyser(groq_config, language='tr')

        logger.info('Fetching channels')
        channels_result = client.fetch_channels()

        if not channels_result.get('success', False):
            logger.error(f"Error fetching channel information: {channels_result.get('errors', 'Unknown error')}")
            sys.exit(1)

        channels = channels_result.get('data', [])
        if not channels:
            logger.warning("No channels found.")
            sys.exit(1)

        logger.info('Displaying available channels')
        print("Available channels:")
        for idx, channel in enumerate(channels, start=1):
            print(f'[{idx}] :: {channel.get("name").upper()}')

        while True:
            try:
                selection = int(input('Please select a channel (1 - {}): '.format(len(channels))))
                if 1 <= selection <= len(channels):
                    break
                else:
                    logger.warning("Invalid selection, please try again.")
                    print("Invalid selection, please try again.")
            except ValueError:
                logger.warning("Invalid input, please enter a number.")
                print("Invalid input, please enter a number.")

        channel_id = channels[selection - 1].get('id')
        channel_name = channels[selection - 1].get('name')

        os.system('cls' if os.name == 'nt' else 'clear')

        logger.info('Displaying message filter options')
        print("Select an option to filter messages:")
        print("1. Messages from the last week")
        print("2. Weekday messages (if today is a weekend)")
        print("3. Today's messages")
        print("4. Messages from the last 6 hours")
        print("5. Messages from the last 2 hours")
        print("6. Messages from the last 2 weeks")
        print("7. Messages from the last month")

        while True:
            try:
                filter_selection = int(input('Select an option (1 - 7): '))
                if 1 <= filter_selection <= 7:
                    break
                else:
                    logger.warning("Invalid selection, please try again.")
                    print("Invalid selection, please try again.")
            except ValueError:
                logger.warning("Invalid input, please enter a number.")
                print("Invalid input, please enter a number.")

        os.system('cls' if os.name == 'nt' else 'clear')

        now = datetime.now()
        if filter_selection == 1:
            oldest = now - timedelta(weeks=1)
        elif filter_selection == 2:
            if now.weekday() >= 5:
                oldest = now - timedelta(days=now.weekday() + 2)
            else:
                oldest = now - timedelta(weeks=1)
        elif filter_selection == 3:
            oldest = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif filter_selection == 4:
            oldest = now - timedelta(hours=6)
        elif filter_selection == 5:
            oldest = now - timedelta(hours=2)
        elif filter_selection == 6:
            oldest = now - timedelta(weeks=2)
        elif filter_selection == 7:
            oldest = now - timedelta(days=30)

        logger.info(f'Fetching messages for channel: {channel_name}')
        messages_result = client.fetch_channel_messages(channel=channel_id, oldest=oldest.timestamp())
        if not messages_result.get('success', False):
            logger.error(f"Error fetching messages: {messages_result.get('errors', 'Unknown error')}")
            sys.exit(1)

        messages = messages_result.get('data', [])
        if not messages:
            logger.warning("No messages found.")
            sys.exit(1)

        logger.info(f'Analyzing {len(messages)} messages from channel: {channel_name}')
        for message in messages:
            response = analyser.analyse(message.get('text'))
            message['analyzes'] = response

        logger.info(f'Saving messages to Parquet file for channel: {channel_name}')
        client.save_messages_to_parquet(messages, channel_name, 'logs')
        logger.info(f"Messages from channel {channel_name} have been successfully saved.")
        print(f"Messages from channel {channel_name} have been successfully saved.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        print(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
