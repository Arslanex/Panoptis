from flask import Flask, request, render_template
from src.groq_client import MessageAnalyser
from config import groq_config
from termcolor import colored
import pandas as pd

app = Flask(__name__)
analyser = MessageAnalyser(groq_config)

def format_analysis(analysis_result):
    result = {
        "Kategori": ["Duygu", "Duygu Güven", "Uygunluk", "Uyg. Güven", "Ton", "Ton Güven", "Aksiyon"],
        "Değer": [
            analysis_result.get("sentiment", {}).get("value", "N/A"),
            analysis_result.get("sentiment", {}).get("confidence", "N/A"),
            analysis_result.get("compliance", {}).get("value", "N/A"),
            analysis_result.get("compliance", {}).get("confidence", "N/A"),
            analysis_result.get("tone", {}).get("value", "N/A"),
            analysis_result.get("tone", {}).get("confidence", "N/A"),
            analysis_result.get("recommended_action", {}).get("value", "N/A"),
        ]
    }

    # Color coding for values (optional, remove termcolor if not needed)
    for idx, value in enumerate(result['Değer']):
        if value == "High":
            result['Değer'][idx] = colored(value, 'green')
        elif value == "Medium":
            result['Değer'][idx] = colored(value, 'yellow')
        elif value == "Low" or value == "Negative":
            result['Değer'][idx] = colored(value, 'red')
        elif value == "Positive":
            result['Değer'][idx] = colored(value, 'green')

    # Convert result to dictionary format for rendering
    df = pd.DataFrame(result)
    return dict(zip(df['Kategori'], df['Değer']))

@app.route('/')
def index():
    return render_template("index.html", title="Message Analyzer")

@app.route('/analyze', methods=['POST'])
def analyze_message():
    user_message = request.form.get("message")
    analysis_result = analyser.analyse(user_message)
    formatted_result = format_analysis(analysis_result)

    # Render the results page with analysis
    return render_template("analyze.html", title="Analysis Results", message=user_message, analysis=formatted_result)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
