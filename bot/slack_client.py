# bot/slack_client.py

import os
import time
from pyexpat.errors import messages

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from utils.logs import Logger
from utils.config import get_env_variable

class SlackClient:
    def __init__(self, token='token'):
        get_env_variable()

        self.token = token
        if not self.token:
            raise ValueError("Slack token'ı bulunamadı. Lütfen geçerli bir token sağlayın veya ortam değişkenini ayarlayın.")

        self.client = WebClient(token= os.getenv('SLACK_BOT_TOKEN'))
        self.logger = Logger().get_logger()

    def list_all_channels(self, max_retries=3):
        retries = 0
        while retries < max_retries:
            try:
                response = self.client.conversations_list(types='public_channel,private_channel')
                if response.get('ok'):
                    channels = [{'id': channel['id'], 'name': channel['name']} for channel in response['channels']]
                    self.logger.info("Tüm kanallar başarıyla listelendi.")
                    return {'success': True, 'data': channels, 'errors': None}
                else:
                    self.logger.error("Beklenmedik bir durum gerçekleştiği için listeleme yapılamadı")
                    return {'success': False, 'data': [], 'errors': None}
            except SlackApiError as e:
                if e.response['error'] == 'ratelimited':
                    retries += 1
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    self.logger.warning(
                        f"Rate limit hatası: Sırasını bekliyor... {retry_after} saniye sonra tekrar denenecek. Deneme: {retries}/{max_retries}")
                    time.sleep(retry_after)
                else:
                    self.logger.error(f"Slack API hatası: {e.response['error']}")
                    return {'success': False, 'datat': [], 'errors': e.response['error']}
        self.logger.error("Maksimum deneme sayısına ulaşıldı. Kanallar listelenemedi.")
        return {'success': False, 'data': [], 'errors': 'ratelimited'}

    def fetch_channel_messages(self, channel, max_retries=3, limit=100, oldest=None, latest=None):
        retries = 0
        while retries < max_retries:
            try:
                response = self.client.conversations_history(channel=channel, limit=limit, oldest=oldest, latest=latest)
                if response.get('ok'):
                    self.logger.info(f"{channel} kanalından {limit} mesaj çekildi.")

                    return {'success': True, 'data': self.clean_messages(response.get('messages')), 'errors': None}
                else:
                    self.logger.error("Beklenmedik bir durum gerçekleştiği için mesajlar çekilemiyor.")
                    return {'success': False, 'data': [], 'errors': None}
            except SlackApiError as e:
                if e.response['error'] == 'ratelimited':
                    retries += 1
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    self.logger.warning(f"Rate limit hatası: Sırasını bekliyor... {retry_after} saniye sonra tekrar denenecek. Deneme: {retries}/{max_retries}")
                    time.sleep(retry_after)
                else:
                    self.logger.error(f"Slack API hatası: {e.response['error']}")
                    return {'success': False, 'data': [], 'errors': e.response['error']}
        self.logger.error("Maksimum deneme sayısına ulaşıldı. Kanallar listelenemedi.")
        return {'success': False, 'datat': [], 'errors': 'ratelimited'}

    @staticmethod
    def clean_messages(messages):
        final_messages = []
        for message in messages:
            if message.get('text') != 'None':
                final_messages.append(message)
        return final_messages

def main():
    slack_client = SlackClient()
    response = slack_client.list_all_channels()
    if response.get('success'):
        print(response.get('data'))
    response = slack_client.fetch_channel_messages('C07TAJVBJFL')
    if response.get('success'):
        print(response.get('data'))
        for message in response.get('data'):
            print(f'User: {message.get("user")} - message: {message.get("text")}')