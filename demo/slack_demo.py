import sys
from config import SLACK_BOT_TOKEN
from src.slack_client import SlackClient
from datetime import datetime, timedelta

def convert_timestamp(ts):
    return datetime.fromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M:%S')

def main():
    try:
        client = SlackClient(SLACK_BOT_TOKEN)
        channels_result = client.fetch_channels()

        if not channels_result.get('success', False):
            print(f"Kanal bilgileri alınırken hata oluştu: {channels_result.get('errors', 'Bilinmeyen hata')}")
            sys.exit(1)

        channels = channels_result.get('data', [])
        if not channels:
            print("Hiçbir kanal bulunamadı.")
            sys.exit(1)

        print("Kullanılabilir kanallar:")
        for idx, channel in enumerate(channels, start=1):
            print(f'[{idx}] :: {channel.get("name").upper()}')

        while True:
            try:
                selection = int(input('Lütfen bir kanal seçiniz (1 - {}): '.format(len(channels))))
                if 1 <= selection <= len(channels):
                    break
                else:
                    print("Geçersiz seçim, lütfen tekrar deneyin.")
            except ValueError:
                print("Geçersiz giriş, lütfen bir sayı girin.")

        channel_id = channels[selection - 1].get('id')
        channel_name = channels[selection - 1].get('name')

        print("Mesajları filtrelemek için bir seçenek seçin:")
        print("1. Son 1 haftanın mesajları")
        print("2. Hafta içi mesajları (eğer bugün haftasonu ise)")
        print("3. Bugünün mesajları")
        print("4. Son 6 saatin mesajları")
        print("5. Son 2 saatin mesajları")

        while True:
            try:
                filter_selection = int(input('Bir seçenek seçin (1 - 5): '))
                if 1 <= filter_selection <= 5:
                    break
                else:
                    print("Geçersiz seçim, lütfen tekrar deneyin.")
            except ValueError:
                print("Geçersiz giriş, lütfen bir sayı girin.")

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

        messages_result = client.fetch_channel_messages(channel=channel_id, oldest=oldest.timestamp())
        if not messages_result.get('success', False):
            print(f"Mesajlar alınırken hata oluştu: {messages_result.get('errors', 'Bilinmeyen hata')}")
            sys.exit(1)

        messages = messages_result.get('data', [])
        if not messages:
            print("Hiçbir mesaj bulunamadı.")
            sys.exit(1)

        client.save_messages_to_parquet(messages, channel_name, 'logs')
        print(f"{channel_name} kanalındaki mesajlar başarıyla kaydedildi.")

    except Exception as e:
        print(f"Bir hata oluştu: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()