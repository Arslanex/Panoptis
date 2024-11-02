import time
import json
from groq import Groq, RateLimitError
from collections import Counter
from utils.logger import CustomLogger


class MessageAnalyser:
    def __init__(self, config, language='en'):
        self._logger = CustomLogger().get_logger()
        self.language = language

        self._client = Groq(api_key=config['api_key'])
        self._logger.info("Initializing MessageAnalyser")

        self._primary_model = config['primary_model']
        self._logger.debug(f'Primary Model: {self._primary_model} initialized')
        self._secondary_model = config['secondary_model']
        self._logger.debug(f'Secondary Model: {self._secondary_model} initialized')
        self._tertiary_model = config['tertiary_model']
        self._logger.debug(f'Tertiary Model: {self._tertiary_model} initialized')
        self._quaternary_model = config["quaternary_model"]
        self._logger.debug(f'Quaternary Model: {self._quaternary_model} initialized')

        self._prompt_group1 = config["prompt_group1"]
        self._logger.debug(f'Prompt Group1: {self._prompt_group1} initialized')
        self._prompt_group2 = config["prompt_group2"]
        self._logger.debug(f'Prompt Group2: {self._prompt_group2} initialized')

    def _send_prompt(self, message, model, prompt,
                     token=300, temperature=0.5, max_retries=3):
        retries = 0
        while retries < max_retries:
            self._logger.debug(f'Starting sending loop {retries}')
            try:
                response = self._client.chat.completions.create(
                    messages=[
                        {'role': 'system', 'content': prompt},
                        {'role': 'user', 'content': message},
                    ],
                    model=model,
                    response_format={"type": "json_object"},
                    max_tokens=token,
                    temperature=temperature,
                    top_p=0.9,
                    frequency_penalty=0.5,
                    presence_penalty=0.6
                )

                if isinstance(response.choices[0].message.content, str):
                    response_content = json.loads(response.choices[0].message.content)
                    if self.language == 'tr':
                        response_content = self._translate_to_turkish(response_content)
                    return response_content
                else:
                    self._logger.error(f'Invalid response from LLM - {model}')
                    return {"error": "Invalid response format"}
            except RateLimitError as e:
                self._logger.warning('Model limit has been exceeded')
                time.sleep(60)
                retries += 1
            except json.JSONDecodeError as e:
                self._logger.error(f"JSON parsing error with model {model}: {e}")
                return {"error": f"JSON parsing failed: {e}"}
        self._logger.error(f"Max retries exceeded")
        return {"error": "Max retries exceeded"}

    def _combine_results(self, *results):
        keys = ['sentiment', 'compliance', 'tone', 'recommended_action']

        combined_result = {}

        self._logger.info(f"Combining results")
        for key in keys:
            value_list = []
            for result in results:
                if isinstance(result, dict) and key in result:
                    value = result[key]
                    if value:
                        value_list.append(value)
                        self._logger.debug('Updated value list')

            most_common_value = Counter(value_list).most_common(1)[0][0] if value_list else "N/A"
            confidence = self._calculate_confidence(value_list)

            combined_result[key] = {
                "value": most_common_value,
                "confidence": confidence
            }

        if self.language == 'tr':
            combined_result = self._translate_to_turkish(combined_result)
        return combined_result

    def _calculate_confidence(self, results):
        self._logger.info('Calculating confidence')
        unique_outputs = len(Counter(results))
        if unique_outputs == 1:
            return "HIGH"
        elif unique_outputs == len(results):
            return "LOW"
        else:
            return "MEDIUM"

    def _translate_to_turkish(self, response):
        translation_map = {
            'Positive': 'Pozitif',
            'Negative': 'Negatif',
            'Neutral': 'Nötr',
            'Aggressive': 'Agresif',
            'Not aggressive': 'Agresif Değil',
            'Formal': 'Resmi',
            'Informal': 'Resmi Olmayan',
            'Neutral': 'Nötr',
            'flag': 'işaretle',
            'clarify': 'açıklığa kavuştur',
            'encourage': 'teşvik et'
        }
        for key in response:
            if isinstance(response[key], dict) and 'value' in response[key]:
                response[key]['value'] = translation_map.get(response[key]['value'], response[key]['value'])
        return response

    def analyse(self, message):

        self._logger.info('Starting message analyse')
        self._logger.debug(f'Message: {message}')
        self._logger.debug(f'Sending value to model 1')
        result1 = self._send_prompt(message, self._primary_model, self._prompt_group1)
        self._logger.debug(f'Sending value to model 2')
        result2 = self._send_prompt(message, self._secondary_model, self._prompt_group2)
        self._logger.debug(f'Sending value to model 3')
        result3 = self._send_prompt(message, self._tertiary_model, self._prompt_group1)
        self._logger.debug(f'Sending value to model 4')
        result4 = self._send_prompt(message, self._quaternary_model, self._prompt_group2)

        results = self._combine_results(result1, result2, result3, result4)
        return results
