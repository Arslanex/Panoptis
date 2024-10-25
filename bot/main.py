# bot/main.py

from slack_client import SlackClient
from analysis import MessageAnalyser

def bot():
    slack_client = SlackClient()
    analyser = MessageAnalyser()

    messages = slack_client.fetch_channel_messages('C07TAJVBJFL').get('data')
    analyser.perform_multiple_toxicity_analysis(messages)

    for message in messages:
        print(f"Status - {message.get('result')} - User: {message.get('user')} - Message: {message.get('text')}")


bot()