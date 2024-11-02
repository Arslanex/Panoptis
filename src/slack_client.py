import re
import time
import logging

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from utils.logger import CustomLogger


class SlackClient:
    def __init__(self, token):
        self._logger = CustomLogger().get_logger()
        if not token:
            self._logger.error("Slack token must be provided")
            raise ValueError("Slack token must be provided")

        self._logger.debug('Slack Client initialized')
        self._client = WebClient(token=token)

    def fetch_channels(self, max_retries=3):
        self._logger.info('Fetching channels')
        retries = 0
        channels = []

        while retries < max_retries:
            self._logger.debug(f'Fetching channels attempt {retries + 1}/{max_retries}')
            try:
                # İlk istekte cursor'u None olarak başlat
                cursor = None

                # next_cursor varsa devam eden bir döngü başlat
                while True:
                    response = self._client.conversations_list(
                        types="public_channel,private_channel,im,mpim",
                        cursor=cursor
                    )

                    if response.get('ok', False):
                        channels.extend([{
                            'idx': len(channels) + idx,
                            'id': channel['id'],
                            'name': channel.get('name', channel.get('user', 'DM/MPIM'))
                        } for idx, channel in enumerate(response.get('channels', []))])

                        # Başka sayfa var mı kontrol et, varsa devam et
                        cursor = response.get('response_metadata', {}).get('next_cursor')
                        if not cursor:
                            break  # Eğer başka sayfa yoksa döngüden çık
                    else:
                        self._logger.warning('Unexpected response while fetching channels')
                        return {'success': False, 'data': [], 'errors': 'unexpected_response'}

                # Başarıyla tüm kanalları çektik, retry döngüsünden çık
                self._logger.info(f'Successfully fetched {len(channels)} channels')
                return {'success': True, 'data': channels, 'errors': None}

            except SlackApiError as e:
                error = e.response.get('error', None)
                if error == 'ratelimited':
                    retries += 1
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    self._logger.warning(f'Rate limited. Retrying after {retry_after} seconds')
                    time.sleep(retry_after)
                else:
                    self._logger.error(f'Error fetching channels: {e.response["error"]}')
                    return {'success': False, 'data': [], 'errors': e.response['error']}

        self._logger.error('Max retries exceeded while fetching channels')
        return {'success': False, 'data': [], 'errors': 'max_retries_exceeded'}

    def fetch_channel_messages(self, channel, max_retries=3, limit=100, inclusive=False, oldest=None, latest=None):
        self._logger.info(f'Fetching messages for channel: {channel}')
        retries = 0
        all_messages = []

        while retries < max_retries:
            self._logger.debug(f'Fetching messages attempt {retries + 1}/{max_retries} for channel: {channel}')
            try:
                # İlk istekte cursor'u None olarak başlat
                cursor = None

                # next_cursor varsa devam eden bir döngü başlat
                while True:
                    response = self._client.conversations_history(
                        channel=channel,
                        inclusive=inclusive,
                        limit=limit,
                        oldest=oldest,
                        latest=latest,
                        cursor=cursor
                    )

                    if response.get('ok', False):
                        messages = response.get('messages', [])
                        for message in messages:
                            message['is_thread_message'] = False
                            all_messages.append(message)

                            # Thread kontrolü yap
                            if 'reply_count' in message and message['reply_count'] > 0:
                                thread_ts = message['ts']
                                self._logger.debug(
                                    f'Fetching thread messages for channel: {channel}, thread_ts: {thread_ts}')
                                thread_response = self.fetch_conversation_replies(channel, thread_ts, max_retries,
                                                                                  limit)
                                if thread_response['success']:
                                    thread_messages = thread_response['data']
                                    for thread_message in thread_messages:
                                        if thread_message['ts'] != thread_ts:
                                            thread_message['is_thread_message'] = True
                                            all_messages.append(thread_message)
                                else:
                                    self._logger.warning(
                                        f'Failed to fetch thread messages for channel: {channel}, thread_ts: {thread_ts}')

                        # next_cursor var mı kontrol et ve varsa devam et
                        cursor = response.get('response_metadata', {}).get('next_cursor')
                        if not cursor:
                            break  # Eğer başka sayfa yoksa döngüden çık
                    else:
                        self._logger.warning(f'Unexpected response while fetching messages for channel: {channel}')
                        return {'success': False, 'data': [], 'errors': 'unexpected_response'}

                # Başarıyla tüm mesajlar çekildiyse retry döngüsünden çık
                self._logger.info(f'Successfully fetched {len(all_messages)} messages for channel: {channel}')
                return {'success': True, 'data': all_messages, 'errors': None}

            except SlackApiError as e:
                error = e.response.get('error', None)
                if error == 'ratelimited':
                    retries += 1
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    self._logger.warning(f'Rate limited. Retrying after {retry_after} seconds for channel: {channel}')
                    time.sleep(retry_after)
                else:
                    self._logger.error(f'Error fetching messages for channel: {channel}, error: {e.response["error"]}')
                    return {'success': False, 'data': [], 'errors': e.response['error']}

        self._logger.error(f'Max retries exceeded while fetching messages for channel: {channel}')
        return {'success': False, 'data': [], 'errors': 'max_retries_exceeded'}

    def fetch_conversation_replies(self, channel, ts, max_retries=3, limit=100, inclusive=False, oldest=None,
                                   latest=None):
        self._logger.info(f'Fetching replies for channel: {channel}, thread_ts: {ts}')
        retries = 0
        all_replies = []

        while retries < max_retries:
            self._logger.debug(
                f'Fetching replies attempt {retries + 1}/{max_retries} for channel: {channel}, thread_ts: {ts}')
            try:
                # İlk istekte cursor'u None olarak başlat
                cursor = None

                # next_cursor varsa devam eden bir döngü başlat
                while True:
                    response = self._client.conversations_replies(
                        channel=channel,
                        ts=ts,
                        inclusive=inclusive,
                        limit=limit,
                        oldest=oldest,
                        latest=latest,
                        cursor=cursor
                    )

                    if response.get('ok', False):
                        replies = response.get('messages', [])
                        all_replies.extend(replies)

                        # next_cursor var mı kontrol et ve varsa devam et
                        cursor = response.get('response_metadata', {}).get('next_cursor')
                        if not cursor:
                            break  # Eğer başka sayfa yoksa döngüden çık
                    else:
                        self._logger.warning(
                            f'Unexpected response while fetching replies for channel: {channel}, thread_ts: {ts}')
                        return {'success': False, 'data': [], 'errors': 'unexpected_response'}

                # Başarıyla tüm cevaplar çekildiyse retry döngüsünden çık
                self._logger.info(f'Successfully fetched replies for channel: {channel}, thread_ts: {ts}')
                return {'success': True, 'data': all_replies, 'errors': None}

            except SlackApiError as e:
                error = e.response.get('error', None)
                if error == 'ratelimited':
                    retries += 1
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    self._logger.warning(
                        f'Rate limited. Retrying after {retry_after} seconds for channel: {channel}, thread_ts: {ts}')
                    time.sleep(retry_after)
                else:
                    self._logger.error(
                        f'Error fetching replies for channel: {channel}, thread_ts: {ts}, error: {e.response["error"]}')
                    return {'success': False, 'data': [], 'errors': e.response['error']}

        self._logger.error(f'Max retries exceeded while fetching replies for channel: {channel}, thread_ts: {ts}')
        return {'success': False, 'data': [], 'errors': 'max_retries_exceeded'}
    def save_messages_to_parquet(self, messages, channel_name, folder_path):
        self._logger.info(f'Saving messages to Parquet for channel: {channel_name}')
        log_data = []
        for msg in messages:
            user_id = msg.get('user', 'N/A')
            is_thread = 'Yes' if msg.get('is_thread_message', False) else 'No'
            ts = msg.get('ts', 'N/A')
            time_str = datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M:%S') if ts != 'N/A' else 'N/A'
            text = msg.get('text', 'N/A')

            # Check for links in the message
            has_link = bool(re.search(r'http[s]?://', text)) if text != 'N/A' else 'N/A'

            # Reply count and like count
            reply_count = str(msg.get('reply_count', 'N/A'))
            like_count = str(sum(reaction.get('count', 0) for reaction in msg.get('reactions', [])) if 'reactions' in msg else 'N/A')

            # LLM analysis results
            analyzes = msg.get('analyzes', 'N/A')
            sentiment = analyzes['sentiment'].get('value') if analyzes != 'N/A' else 'N/A'
            compliance = analyzes['compliance'].get('value') if analyzes != 'N/A' else 'N/A'
            tone = analyzes['tone'].get('value') if analyzes != 'N/A' else 'N/A'
            recommended_action = analyzes['recommended_action'].get('value') if analyzes != 'N/A' else 'N/A'

            log_data.append({
                "Date": time_str,
                "User": user_id,
                "Thread": is_thread,
                "Message": text,
                "Has Link": has_link,
                "Reply Count": reply_count,
                "Like Count": like_count,
                "Sentiment": sentiment,
                "Community Compliance": compliance,
                "Language Tone": tone,
                "Recommended Action": recommended_action
            })

        # Create DataFrame and write to Parquet
        df = pd.DataFrame(log_data)
        file_name = f"{folder_path}/{channel_name}_{datetime.now().strftime('%Y%m%d')}.parquet"
        table = pa.Table.from_pandas(df)
        pq.write_table(table, file_name)
        self._logger.info(f'Messages saved to {file_name}')
        print(f"Messages saved to {file_name}")
