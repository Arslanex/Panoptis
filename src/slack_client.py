import re
import time
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

class SlackClient:
    def __init__(self, token):
        if not token:
            raise ValueError("Slack token must be provided")

        self._client = WebClient(token=token)

    def fetch_channels(self, max_retries=3):
        retries = 0
        while retries < max_retries:
           try:
               response = self._client.conversations_list(types='public_channel,private_channel')
               if response.get('ok', False):
                   channels = [{'idx': idx, 'id': channel['id'], 'name': channel['name']}
                               for idx, channel in enumerate(response.get('channels', []))]
                   return {'success': True, 'data': channels, 'errors': None}
               else:
                   return {'success': False, 'data': [], 'errors': 'unexpected_response'}
           except SlackApiError as e:
               error = e.response.get('error', None)
               if  error == 'ratelimited':
                   retries += 1
                   retry_after = int(e.response.headers.get('Retry-After', 60))
                   time.sleep(retry_after)
               else:
                   return {'success': False, 'data': [], 'errors': e.response['error']}
        return {'success': False, 'data': [], 'errors': 'max_retries_exceeded'}

    def fetch_channel_messages(self, channel, max_retries=3, limit=100, inclusive=False, oldest=None, latest=None):
        retries = 0
        while retries < max_retries:
            try:
                response = self._client.conversations_history(channel=channel, inclusive=inclusive, limit=limit, oldest=oldest)
                if response.get('ok', False):
                    messages = response.get('messages', [])
                    all_messages = []
                    for message in messages:
                        message['is_thread_message'] = False  # Ana mesaj olduğunu belirt
                        all_messages.append(message)

                        # Mesajın altında thread var mı kontrol et
                        if 'reply_count' in message and message['reply_count'] > 0:
                            thread_ts = message['ts']
                            thread_response = self.fetch_conversation_replies(channel, thread_ts, max_retries, limit)
                            if thread_response['success']:
                                thread_messages = thread_response['data']
                                for thread_message in thread_messages:
                                    if thread_message['ts'] != thread_ts:  # Ana mesajı tekrar eklememek için
                                        thread_message['is_thread_message'] = True  # Thread mesajı olduğunu belirt
                                        all_messages.append(thread_message)
                            else:
                                # Thread mesajlarını çekerken hata oluştuysa işle
                                pass  # İsterseniz loglama veya hata yönetimi yapabilirsiniz
                    return {'success': True, 'data': all_messages, 'errors': None}
                else:
                    return {'success': False, 'data': [], 'errors': 'unexpected_response'}
            except SlackApiError as e:
                error = e.response.get('error', None)
                if error == 'ratelimited':
                    retries += 1
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    time.sleep(retry_after)
                else:
                    return {'success': False, 'data': [], 'errors': e.response['error']}
        return {'success': False, 'data': [], 'errors': 'max_retries_exceeded'}

    def fetch_conversation_replies(self, channel, ts, max_retries=3, limit=100, inclusive=False, oldest=None, latest=None):
        retries = 0
        while retries < max_retries:
            try:
                response = self._client.conversations_replies(
                    channel=channel,
                    ts=ts,
                    inclusive=inclusive,
                    limit=limit,
                    oldest=oldest,
                    latest=latest
                )
                if response.get('ok', False):
                    return {'success': True, 'data': response.get('messages', []), 'errors': None}
                else:
                    return {'success': False, 'data': [], 'errors': 'unexpected_response'}
            except SlackApiError as e:
                error = e.response.get('error', None)
                if error == 'ratelimited':
                    retries += 1
                    retry_after = int(e.response.headers.get('Retry-After', 60))
                    time.sleep(retry_after)
                else:
                    return {'success': False, 'data': [], 'errors': e.response['error']}
        return {'success': False, 'data': [], 'errors': 'max_retries_exceeded'}

    def save_messages_to_parquet(self, messages, channel_name):
        """Verilen mesajları analiz sonuçları ile birlikte kanal adı ve tarihe göre Parquet dosyasına kaydeder."""
        log_data = []
        for msg in messages:
            user_id = msg.get('user', 'N/A')
            is_thread = 'Evet' if msg.get('is_thread_message', False) else 'Hayır'
            ts = msg.get('ts', 'N/A')
            time_str = datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M:%S') if ts != 'N/A' else 'N/A'
            text = msg.get('text', 'N/A')

            # Mesajdaki link durumu
            has_link = bool(re.search(r'http[s]?://', text)) if text != 'N/A' else 'N/A'

            # Yanıt sayısı ve beğeni bilgisi, yoksa "N/A"
            reply_count = str(msg.get('reply_count', 'N/A'))
            like_count = str(sum(reaction.get('count', 0) for reaction in msg.get('reactions', [])) if 'reactions' in msg else 'N/A')

            # LLM analiz sonuçları
            sentiment = msg.get("sentiment", "N/A")
            compliance = msg.get("compliance", "N/A")
            keywords = ", ".join(msg.get("keywords", ["N/A"]))
            tone = msg.get("tone", "N/A")
            recommended_action = msg.get("recommended_action", "N/A")

            log_data.append({
                "Tarih": time_str,
                "Kullanıcı": user_id,
                "Thread": is_thread,
                "Mesaj": text,
                "Link Var mı": has_link,
                "Yanıt Sayısı": reply_count,
                "Beğeni Sayısı": like_count,
                "Duygu": sentiment,
                "Topluluk Uyum": compliance,
                "Anahtar Kelimeler": keywords,
                "Dil Tarzı": tone,
                "Önerilen Aksiyon": recommended_action
            })

        # DataFrame oluştur ve Parquet dosyasına yaz
        df = pd.DataFrame(log_data)

        file_name = f"{channel_name}_{datetime.now().strftime('%Y%m%d')}.parquet"
        table = pa.Table.from_pandas(df)
        pq.write_table(table, file_name)
        print(f"Mesajlar {file_name} dosyasına kaydedildi.")