import os
import json
from openai import OpenAI
from logger_config import logger

# Initialize OpenAI Client explicitly using the Env Var
# This is the "New Way" as per your request
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_transcript(utterances: list) -> dict:
    """
    Sends the transcript to OpenAI (GPT-4o-mini) for psychological analysis.
    
    Args:
        utterances: List of dicts [{'speaker': 'A', 'text': '...'}, ...]
    
    Returns:
        A dictionary containing the structured analysis (JSON).
    """
    
    # 1. Format the input for the LLM
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
    3. Summary: Provide a brief summary of the session.

    You MUST output the result in valid JSON format with the following structure:
    {
        "roles": {"therapist": "Speaker X", "patient": "Speaker Y"},
        "summary": "...",
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
            response_format={"type": "json_object"},  # Force JSON output
            temperature=0.7
        )

        # Accessing content in SDK v1.x uses dot notation (Pydantic model)
        # using ["content"] would raise a TypeError in this version.
        content = response.choices[0].message.content
        
        # Parse JSON string to Python dict
        result = json.loads(content)
        
        logger.info("Successfully received analysis from OpenAI.")
        return result

    except Exception as e:
        logger.error(f"Error during OpenAI analysis: {e}")
        raise