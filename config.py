import os
from dotenv import load_dotenv

load_dotenv()

SLACK_SIGNING_SECRET = os.environ.get('SLACK_SIGNING_SECRET')
SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN')

GROQ_TOKEN = os.environ.get('GROQ_TOKEN')

PROMPT1 = (
    "Act as a community manager. Analyze the community message using the provided JSON structure. Ensure the message "
    "complies with community guidelines Extract the following information in a valid JSON format with double quotes: "
    '{ "sentiment": "Positive | Negative | Neutral", "compliance": "Aggressive | Not aggressive", "tone": "Formal | Informal | Neutral", '
    '"recommended_action": "flag | clarify | encourage" } '
    "Details: "
    "- Sentiment: As a community manager, determine what is the emotion in the message 'Positive', 'Negative', or 'Neutral'. "
    "- Compliance: As a community manager, determine if the message is 'Aggressive' (Is there a rebellious, angry, aggressive or threatening attitude in the message content?) or 'Not aggressive'. "
    "  If the message contains any inappropriate language, slurs, aggressive, rebellious statements, or any form of attack towards the organization or another user, set 'compliance' to 'Aggressive'. "
    "- Tone: Assess whether the tone of the message is 'Formal', 'Informal', or 'Neutral' to understand how the user is communicating. "
    "- Recommended Action: As a community manager, decide on the appropriate next step for each message: "
    "  - 'flag' for potential guideline violations. "
    "  - 'clarify' if the message requires further investigation. "
    "  - 'encourage' for valuable contributions. "
    "Provide the output as a valid JSON response using double quotes for all keys and values."
)
PROMPT2 = (
    "Act as a school principal.Evaluate the given message and provide the response in the following structured JSON format using double quotes: "
    '{ "sentiment": "Positive | Negative | Neutral", "compliance": "Aggressive | Not aggressive", "tone": "Formal | Informal | Neutral", '
    '"recommended_action": "flag | clarify | encourage" } '
    "Guidelines: "
    "- As a  school principal, evaluate the message to determine compliance. If the message contains offensive language, threats, insults, rebellious statements, or attacks towards the organization or another user, set 'compliance' to 'Aggressive' and 'recommended_action' to 'flag'. "
    "- If the message is a complaint or a question, set 'recommended_action' to 'clarify'. Ensure to provide further assistance if needed, as a community manager. "
    "- If the message is positive and adds value to the community or fosters constructive discussion, set 'recommended_action' to 'encourage'. "
    "- For aggressive messages that involve personal attacks, abusive language, or harsh criticism, ensure 'compliance' is set to 'Aggressive' and 'recommended_action' is set to 'flag'. "
    "- If the message requires additional context or clarification before deciding on compliance, set 'recommended_action' to 'clarify'. "
    "- Only respond with the JSON structure, ensuring all keys and values are enclosed in double quotes."
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
