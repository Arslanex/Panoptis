# bot/analysis.py

import os
import time
import json
import tiktoken
from groq import Groq

from utils.logs import Logger
from utils.config import get_env_variable

class MessageAnalyser:
    def __init__(self):
        get_env_variable()
        self.logger = Logger().get_logger()
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        self.token = os.getenv('GROQ_TOKEN')
        self.client = Groq(api_key=self.token)
        self.logger.debug("Groq Clien olşturuldu.")

        with open('../config/config.json', 'r') as f:
            config = json.load(f)

        self.model1 = config.get("groq_params").get("model1")
        self.model2= config.get("groq_params").get("model2")
        self.backup_model1 = config.get("groq_params").get("backup1")
        self.backup_model2 = config.get("groq_params").get("backup2")
        self.max_requests_per_minute = config.get("groq_params").get("max_request_per_minute")
        self.max_tokens_per_minute = config.get("groq_params").get("max_tokens_per_minute")

        self.requests_made = 0
        self.tokens_used = 0
        self.start_time = None

    @staticmethod
    def create_message(text):
        return {"role": "user", "content": text}

    def get_token_count(self, text):
        return len(self.tokenizer.encode(text))

    def manage_rate_limit(self, tokens_needed):
        if self.start_time is None:
            self.start_time = time.time()

        current_time = time.time()
        elapsed_time = current_time - self.start_time

        if elapsed_time >= 60:
            self.requests_made = 0
            self.tokens_used = 0
            self.start_time = current_time

        if self.requests_made >= self.max_requests_per_minute or self.tokens_used >= self.max_tokens_per_minute:
            wait_time = 60 - elapsed_time
            self.logger.info(f"Oran limitine ulaşıldı, {wait_time:.2f} saniye bekleniyor...")
            time.sleep(wait_time)

            self.requests_made = 0
            self.tokens_used = 0
            self.start_time = time.time()

        self.requests_made += 1
        self.tokens_used += tokens_needed

    def perform_toxicity_analysis(self, text, model=None):
        if model == None:
            model = self.model1

        message = self.create_message(text)
        tokens_needed = self.get_token_count(text)
        self.manage_rate_limit(tokens_needed)
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role":"system",
                     "content": "Sen bir toksisite tespit modelisin. Metindeki ifadelerin başka bir bireye veya kuruma "
                                "gereğinden fazla agresif, saldırgan, aşağılayıcı veya uygunsuz olup olmadığını analiz "
                                "et. Cevabın sadece 'evet' veya 'hayır' olmalıdır. Mesaj toksik ise 'evet', değilse "
                                "'hayır' olarak yanıt ver."
                     }, message
                ],
                model=model,
            )
            self.logger.debug(f"Verilen metin çıktısı başarı ile {model} modelinden alındı.")
            self.logger.info(f"Verilen metin sistem tarafından {"'SALDIRGAN'1" if response.choices[0].message.content.capitalize() == 'Evet' else "'SALDIRGAN DEĞİL'" } olarak sınıflandırıldı")
            return {'success': True, 'data': response.choices[0].message.content, 'error': None}
        except Exception as e:
            self.logger.error(f"İstek sırasında beklenmedik bir hata oluştu: {e}")
        if model != self.backup_model1:
            self.logger.info(f"Backup modeli olan '{self.backup_model1}' ile işlem yeniden deneniyor")
            return self.perform_toxicity_analysis(text, model=self.backup_model1)
        else:
            self.logger.info(f"İşlem başarısız oldu.")
            return {'success': False, 'data': None, 'error': None}

    def perform_multiple_toxicity_analysis(self, text_list, model="llama3-8b-8192"):
        for item in text_list:
            text = item.get("text", "None")
            result = self.perform_toxicity_analysis(text, model=model)
            if result.get('success'):
                item['result'] = result.get('data')
            else:
                item['result'] = "N/A"
        return {'success': True, 'data': None, 'error': None}


def main():
    analyser = MessageAnalyser()
    response = analyser.perform_toxicity_analysis("Hello World")
    if response.get('success'):
        print(response.get('data'))

    response = analyser.perform_toxicity_analysis("Çok saçma bir işçilik, iş yapmayı bilmiyorlar. Hakkımı yediler.")
    if response.get('success'):
        print(response.get('data'))
