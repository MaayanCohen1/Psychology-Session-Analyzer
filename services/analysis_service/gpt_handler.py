import os
import json
from openai import OpenAI
from logger_config import logger

# Initialize OpenAI Client explicitly
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_transcript(utterances: list) -> dict:
    """
    Sends the transcript to OpenAI (GPT-4o-mini) for psychological analysis.
    """
    
    # 1. Format input
    formatted_transcript = ""
    for item in utterances:
        formatted_transcript += f"Speaker {item['speaker']}: {item['text']}\n"

    # 2. Define the System Prompt
    system_instruction = """
    You are an expert psychotherapist and data analyst.
    Your task is to analyze a transcript of a therapy session.

    Please perform the following tasks:
    1. Identify Roles: Determine who is the 'Therapist' and who is the 'Patient'.
    2. Analyze Utterances: For each sentence, identify the primary 'emotion' and the main 'topic'.
    3. Clinical Insights: Based on the topics that triggered negative or positive emotions, provide a list of 2-3 recommendations for the therapist for the next session.

    You MUST output the result in valid JSON format with the following structure:
    {
        "roles": {"therapist": "Speaker X", "patient": "Speaker Y"},
        "summary": "Brief summary of the session content.",
        "clinical_recommendations": [
            "Recommendation 1...",
            "Recommendation 2..."
        ],
        "analysis": [
            {
                "speaker": "Speaker X",
                "text": "...",
                "emotion": "...",
                "topic": "..."
            }
        ]
    }
    """

    try:
        logger.info("Sending transcript to OpenAI for analysis...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Here is the transcript:\n{formatted_transcript}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )

        content = response.choices[0].message.content
        result = json.loads(content)
        
        logger.info("Successfully received analysis from OpenAI.")
        return result

    except Exception as e:
        logger.error(f"Error during OpenAI analysis: {e}")
        raise