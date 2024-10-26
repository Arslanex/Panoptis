# bot/slack_client.py

import os
import time
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from utils.logs import Logger
from utils.config import get_env_variable


class SlackClient:
    def __init__(self, token='token'):
        get_env_variable()

        self.token = token
        if not self.token:
            raise ValueError("Slack token bulunamadı. Geçerli bir token sağlayın veya ortam değişkenini ayarlayın.")

        self.client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
        self.logger = Logger().get_logger()

        self.logger.info("SlackClient initialized successfully with token.")

    def list_all_channels(self, max_retries=3):
        retries = 0
        self.logger.info("Listing all Slack channels...")

        while retries < max_retries:
            try:
                response = self.client.conversations_list(types='public_channel,private_channel')
                if response.get('ok'):
                    channels = [{'id': channel['id'], 'name': channel['name']} for channel in response['channels']]
                    self.logger.info(f"Successfully listed {len(channels)} channels.")
                    return {'success': True, 'data': channels, 'errors': None}
                else:
                    self.logger.error("Failed to list channels due to an unexpected response: %s", response)
                    return {'success': False, 'data': [], 'errors': 'unexpected_response'}
            except SlackApiError as e:
                if e.response['error'] == 'ratelimited':
                    retries += 1
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    self.logger.warning(
                        f"Rate limit exceeded. Retrying in {retry_after} seconds. Attempt {retries}/{max_retries}.")
                    time.sleep(retry_after)
                else:
                    self.logger.error(f"Slack API error while listing channels: {e.response['error']}")
                    return {'success': False, 'data': [], 'errors': e.response['error']}

        self.logger.error("Max retries reached. Failed to list channels.")
        return {'success': False, 'data': [], 'errors': 'max_retries_exceeded'}

    def fetch_channel_messages(self, channel, max_retries=3, limit=100, oldest=None, latest=None):
        retries = 0
        self.logger.info(f"Fetching messages from channel {channel} with limit {limit}.")

        while retries < max_retries:
            try:
                response = self.client.conversations_history(
                    channel=channel, limit=limit, oldest=oldest, latest=latest
                )
                if response.get('ok'):
                    self.logger.info(f"Successfully fetched {len(response['messages'])} messages from {channel}.")
                    return {
                        'success': True,
                        'data': self.clean_messages(response.get('messages')),
                        'errors': None
                    }
                else:
                    self.logger.error(f"Unexpected response while fetching messages from {channel}: {response}")
                    return {'success': False, 'data': [], 'errors': 'unexpected_response'}
            except SlackApiError as e:
                if e.response['error'] == 'ratelimited':
                    retries += 1
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    self.logger.warning(
                        f"Rate limit exceeded. Retrying in {retry_after} seconds. Attempt {retries}/{max_retries}.")
                    time.sleep(retry_after)
                else:
                    self.logger.error(f"Slack API error while fetching messages from {channel}: {e.response['error']}")
                    return {'success': False, 'data': [], 'errors': e.response['error']}

        self.logger.error(f"Max retries reached. Failed to fetch messages from {channel}.")
        return {'success': False, 'data': [], 'errors': 'max_retries_exceeded'}

    @staticmethod
    def clean_messages(messages):
        final_messages = [msg for msg in messages if msg.get('text') != 'None']
        return final_messages


def main():
    slack_client = SlackClient()

    # Listing all channels
    response = slack_client.list_all_channels()
    if response.get('success'):
        print("Channels:", response.get('data'))
    else:
        print(f"Error listing channels: {response.get('errors')}")

    # Fetching messages from a specific channel
    response = slack_client.fetch_channel_messages('C07TAJVBJFL')
    if response.get('success'):
        print("Messages from channel:")
        for message in response.get('data'):
            print(f'User: {message.get("user")} - Message: {message.get("text")}')
    else:
        print(f"Error fetching messages: {response.get('errors')}")
