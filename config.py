import os
from dotenv import load_dotenv

load_dotenv()

SLACK_SIGNING_SECRET = os.environ.get('SLACK_SIGNING_SECRET')
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')


GROQ_TOKEN = os.environ.get('GROQ_TOKEN')
PROMPT1 = (
            "Analyze the following message with this JSON structure. Each field must include a confidence score "
            "as 'High', 'Medium', or 'Low'. The structure: { 'sentiment': { 'value': 'Positive | Negative | Neutral', "
            "'confidence': 'High | Medium | Low' }, 'compliance': { 'value': 'Y | N', 'confidence': 'High | Medium | Low' }, "
            "'keywords': ['List', 'of', 'keywords'], 'tone': { 'value': 'Formal | Informal | Neutral', "
            "'confidence': 'High | Medium | Low' }, 'recommended_action': 'Suggested action.' } Respond only with JSON. "
            "If the message contains any kind of insult, offensive language, threat, or attack towards the community or any individual in the community, the compliance value must be 'N'. "
            "Additionally, if the message is a complaint or question, the recommended action should be 'Reach out to the user'. "
            "If the message contains offensive or aggressive language, the recommended action should be 'Review and investigate'."
        )
PROMPT2 = (
            "Assess the following text in structured JSON format as follows: { 'sentiment': { 'status': 'Positive | "
            "Negative | Neutral', 'confidence_score': 'High | Medium | Low' }, 'compliance': { 'status': 'Y | N', "
            "'confidence_score': 'High | Medium | Low' }, 'keywords': ['Key phrases'], 'tone': { 'style': "
            "'Formal | Informal | Neutral', 'confidence_score': 'High | Medium | Low' }, 'recommended_action': "
            "'Recommended next step for the manager.' } Respond with only the JSON structure. "
            "If the message contains any kind of insult, offensive language, threat, or attack towards the community or any individual in the community, the compliance value must be 'N'. "
            "Additionally, if the message is a complaint or question, the recommended action should be 'Reach out to the user'. "
            "If the message contains offensive or aggressive language, the recommended action should be 'Review and investigate'."
        )

groq_config = {
    "api_key": GROQ_TOKEN,
    "primary_model": "llama3-70b-8192",
    "secondary_model": "gemma2-9b-it",
    "tertiary_model": "llama-3.1-70b-versatile",
    "quaternary_model": "llama3-8b-8192",
    "prompt_group1": PROMPT1,
    "prompt_group2": PROMPT2
}

