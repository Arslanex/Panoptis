# bot/analysis.py


from utils.logs import Logger
from groq import Groq
import requests


class MessageAnalyser:
    def __init__(self, config) -> None:
        self._logger = Logger().get_logger()

        token = config.token
        if not token:
            self._logger.error("GROQ_TOKEN is not set. Please check your environment variables.")
            raise ValueError("Missing GROQ_TOKEN environment variable")

        self._client = Groq(api_key=token)
        self._logger.debug("Groq Client initialized.")

        self._model1 = config.model1
        self._model2 = config.model2
        self._backup_model = config.backup_model

        if not self._model1 or not self._backup_model:
            self._logger.error("Model configurations are missing in config.json.")
            raise ValueError("Missing model configurations in config.json")

    @staticmethod
    def _generate_message_payload(text="N/A"):
        return {"role": "user", "content": text}

    @staticmethod
    def _batch_messages(messages, max_token_limit):
        current_batch = []
        current_token_count = 0
        batches = []

        for message in messages:
            token_count = len(message['text'].split()) if 'text' in message else 0
            if current_token_count + token_count > max_token_limit:
                batches.append(current_batch)
                current_batch = [message]
                current_token_count = token_count
            else:
                current_batch.append(message)
                current_token_count += token_count

        if current_batch:
            batches.append(current_batch)

        return batches

    def perform_toxicity_analysis(self, text, model=None):
        if model is None:
            model = self._model1

        message_payload = self._generate_message_payload(text)

        try:
            response = self._client.chat.completions.create(
                messages=[
                    {"role": "system",
                     "content": "Analyze the given message as a community administrator and determine whether it is "
                                "compliant with community guidelines or not. Specifically, does the message contain any "
                                "harmful, offensive, or inappropriate content towards individuals or groups, include "
                                "any offensive language, or have any aggressive tone? If the message contains any "
                                "harmful or offensive content, please respond with 'Y', otherwise respond with 'N'. "
                                "Only with 'Y' or 'N'"
                     },
                    message_payload
                ],
                model=model,
            )

            self._logger.debug(f"Successfully received response from model {model}.")
            is_toxic = response.choices[0].message.content.strip().capitalize()
            self._logger.info(f"Text classified as {'TOXIC' if is_toxic == 'E' else 'NOT TOXIC'} by the system.")
            return {'success': True, 'data': is_toxic, 'error': None}

        except requests.exceptions.RequestException as e:
            self._logger.error(f"Unexpected error during the request: {e}")
            if model != self._backup_model:
                self._logger.info(f"Retrying with backup model '{self._backup_model}'...")
                return self.perform_toxicity_analysis(text, model=self._backup_model)
            else:
                self._logger.info("Operation failed.")
                return {'success': False, 'data': None, 'error': str(e)}
        except Exception as e:
            self._logger.error(f"An unexpected error occurred: {e}")
            self._logger.info("Operation failed.")
            return {'success': False, 'data': None, 'error': str(e)}

    def perform_multiple_toxicity_analysis(self, text_list, model=None):
        if model is None:
            model = self._model1

        results = []
        for item in text_list:
            text = item.get("text", "")
            if not text:
                self._logger.warning("No text provided for analysis in one of the items.")
                results.append({'text': text, 'result': "N/A"})
                continue

            result = self.perform_toxicity_analysis(text, model=model)
            item.update({'result': result.get('data', "N/A")})
            results.append(item)

        return {'success': True, 'data': results, 'error': None}

    def perform_batch_analysis(self, messages, max_token_limit=15000):
        batches = self._batch_messages(messages, max_token_limit)
        summaries = []

        for index, batch in enumerate(batches):
            self._logger.info(f"Processing batch {index + 1}/{len(batches)} with {len(batch)} messages.")
            concatenated_text = ' '.join([message['text'] for message in batch])

            try:
                response = self._client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "Summarize the provided text summaries from the community channels"
                                                      " of the 'Game and Application Academy' and identify key points "
                                                      "that a community manager should prioritize. Highlight the needs "
                                                      "of community members, questions, and requests for answers that "
                                                      "are most relevant to the majority of users who log in. Provide an "
                                                      "accurate and concise summary that extracts essential information."},
                        {"role": "user", "content": concatenated_text}
                    ],
                    model=self._model1
                )
                summary = response.choices[0].message.content.strip()
                summaries.append(summary)
            except requests.exceptions.RequestException as e:
                self._logger.error(f"Failed to get response for batch {index + 1}: {e}")
                summaries.append("Error: Failed to get response")

            return {'success': True, 'data': summaries, 'error': None}


def main():
    config = Config()
    analyser = MessageAnalyser(config)

    # Example analysis for single text
    response = analyser.perform_toxicity_analysis("Hello World")
    if response.get('success'):
        print(f"Result: {response.get('data')}")

    # Example analysis for potentially toxic text
    response = analyser.perform_toxicity_analysis("Çok saçma bir işçilik, iş yapmayı bilmiyorlar. Hakkımı yediler.")
    if response.get('success'):
        print(f"Result: {response.get('data')}")

    # Example analysis for multiple texts
    text_list = [
        {"text": "Merhaba, nasılsınız?"},
        {"text": "Bu işi çok kötü yaptınız, hiç memnun kalmadım."},
        {"text": "Buraya geldiğim için hiç mutlu değilim."},
        {"text": "Bir daha buraya yazarsan sen o zaman görürüsün."}
    ]
    response = analyser.perform_multiple_toxicity_analysis(text_list)
    if response.get('success'):
        for result in response.get('data', []):
            print(f"Text: {result['text']}, Result: {result['result']}")

