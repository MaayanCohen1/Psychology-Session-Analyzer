import os
import json
from openai import OpenAI
from logger_config import logger

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_transcript(utterances: list) -> dict:
    formatted_transcript = ""
    for item in utterances:
        formatted_transcript += f"Speaker {item['speaker']}: {item['text']}\n"

    system_instruction = """
    You are an expert clinical psychologist and data analyst specialized in Trauma and CBT.
    Analyze the following therapy session transcript.

    Perform these specific tasks:
    
    1. **Identify Roles**: Who is 'Therapist' and who is 'Patient'?
    
    2. **Trauma & PTSD Indicators**: Scan the text for specific markers of PTSD based on DSM-5 criteria:
       - Intrusive thoughts/Flashbacks
       - Avoidance of triggers
       - Negative alterations in cognition/mood
       - Hyperarousal/Reactivity
       If found, list them. If not, return an empty list.
    
    3. **Risk Assessment**: Check for self-harm or suicide risk. Return boolean.
    
    4. **Cognitive Distortions**: Identify CBT distortions (e.g., Catastrophizing, Black-and-white thinking).
    
    5. **Clinical Recommendations**: Provide 3 actionable recommendations for the therapist.

    6. **Sentence Analysis**: Emotion, Sentiment (-1 to 1), and Topic for each sentence.

    Output MUST be valid JSON:
    {
        "roles": {"therapist": "Speaker X", "patient": "Speaker Y"},
        "summary": "Brief session summary...",
        "ptsd_analysis": {
            "is_trauma_related": true,
            "detected_symptoms": ["Avoidance", "Hyperarousal"],
            "notes": "Patient refuses to discuss the accident details."
        },
        "risk_assessment": {
            "has_risk": false,
            "details": "..."
        },
        "cognitive_distortions": ["Catastrophizing"],
        "clinical_recommendations": ["...", "..."],
        "analysis": [
            {
                "speaker": "Speaker X",
                "text": "...",
                "emotion": "...",
                "sentiment_score": -0.5,
                "topic": "..."
            }
        ]
    }
    """

    try:
        logger.info("Sending trauma-informed transcript to OpenAI...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Transcript:\n{formatted_transcript}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )

        content = response.choices[0].message.content
        result = json.loads(content)
        
        logger.info("Successfully received analysis.")
        return result

    except Exception as e:
        logger.error(f"Error during OpenAI analysis: {e}")
        raise