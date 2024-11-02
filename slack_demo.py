
from config import SLACK_BOT_TOKEN
from src.slack_client import SlackClient
from datetime import datetime

def convert_timestamp(ts):
    """Slack timestamp formatını okunabilir datetime formatına çevirir."""
    return datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M:%S')

def main():
    # Slack Bot Tokenınızı ortam değişkeninden alabilirsiniz veya doğrudan burada tanımlayabilirsiniz.
    # Güvenlik açısından, token'ınızı doğrudan kodda tutmamanızı öneririm. # Buraya kendi token'ınızı ekleyin

    slack_client = SlackClient(token=SLACK_BOT_TOKEN)

    # Kanal ID'sini buraya ekleyin veya dinamik olarak seçmek için fetch_channels metodunu kullanın
    CHANNEL_ID = 'C07TAJVBJFL'  # Örneğin: 'C1234567890'

    # Kanal adını almak için fetch_channels metodunu kullanıyoruz
    channels_result = slack_client.fetch_channels()
    channel_name = next((ch['name'] for ch in channels_result['data'] if ch['id'] == CHANNEL_ID), 'Unknown_Channel')

    # Kanal mesajlarını çek ve dosyaya kaydet
    messages_result = slack_client.fetch_channel_messages(channel=CHANNEL_ID)
    if messages_result['success']:
        messages = messages_result['data']
        slack_client.save_messages_to_parquet(messages, channel_name)
    else:
        print(f"Mesajlar alınırken hata oluştu: {messages_result['errors']}")


if __name__ == "__main__":
    main()

