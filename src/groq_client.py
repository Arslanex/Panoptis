import time
import json
from pyexpat.errors import messages
from sys import modules

import requests
from groq import Groq
from collections import Counter


class MessageAnalyser:
    def __init__(self, config):
        self._client = Groq(api_key=config['api_key'])

        self._primary_model = config['primary_model']
        self._secondary_model = config['secondary_model']
        self._tertiary_model = config['tertiary_model']
        self._quaternary_model = config["quaternary_model"]

        self._prompt_group1 = config["prompt_group1"]
        self._prompt_group2 = config["prompt_group2"]

    def _send_prompt(self, message, model, prompt,
                     token=300, temperature=0.5, max_retries=3):
        reties = 0
        while reties < max_retries:
            try:
                response = self._client.chat.completions.create(
                    messages=[
                        {'role':'system', 'content':prompt},
                        {'role':'user', 'content':message},
                    ],
                    model = model,
                    response_format={"type": "json_object"},
                    max_tokens=token,
                    temperature=temperature
                )

                if isinstance(response.choices[0].message.content, str):
                    return json.loads(response.choices[0].message.content)
                else:
                    return {"error": "Invalid response format"}
            except requests.exceptions.RequestException as e:
                if e.response is not None and e.response.status_code == 429:
                    retry_after = e.response.headers.get('Retry-After', 60)
                    time.sleep(retry_after)
                    reties += 1
                else:
                    print(f"Request error with model {model}: {e}")
                    return {"error": "Invalid response format"}
            except json.JSONDecodeError as e:
                print(f"JSON parsing error with model {model}: {e}")
                return {"error": f"JSON parsing failed: {e}"}
        return {"error": "Max retries exceeded"}

    def _combine_results(self, *results):
        keys = ['sentiment', 'compliance', 'tone', 'recommended_action']

        combined_result = {}

        for key in keys:
            value_list = []
            for result in results:
                if isinstance(result, dict) and key in result and isinstance(result[key], dict):
                    value = result[key].get('value') or result[key].get('type') or result[key].get('status')
                    if value:
                        value_list.append(value)

            most_common_value = Counter(value_list).most_common(1)[0][0] if value_list else "N/A"
            confidence = self._calculate_confidence(value_list)

            combined_result[key] = {
                "value": most_common_value,
                "confidence": confidence
            }

        return combined_result

    def _calculate_confidence(self, results):
        unique_outputs = len(Counter(results))
        if unique_outputs == 1:
            return "HIGH"
        elif unique_outputs == len(results):
            return "LOW"
        else:
            return "MEDIUM"

    def analyse(self, message):
        result1 = self._send_prompt(message, self._primary_model, self._prompt_group1)
        result2 = self._send_prompt(message, self._secondary_model, self._prompt_group2)
        result3 = self._send_prompt(message, self._tertiary_model, self._prompt_group1)
        result4 = self._send_prompt(message, self._quaternary_model, self._prompt_group2)

        results = self._combine_results(result1, result2, result3, result4)
        return results