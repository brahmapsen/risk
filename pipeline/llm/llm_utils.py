import os
from openai import OpenAI
from dotenv import load_dotenv

env_path = os.path.abspath(".env")
print("Trying to load .env from:", env_path)
load_dotenv()

def get_llm():
    """
    Generic LLM client wrapper.
    Works with OpenAI API, AIML API, Groq API (OpenAI-compatible).
    """
    
    api_key = os.environ["AIML_API_KEY"] ##os.getenv("LLM_API_KEY")
    base_url="https://api.aimlapi.com/v1"
    model = "gpt-4o-mini"

    if not api_key:
        raise ValueError("Missing LLM_API_KEY environment variable")

    # openai_client = OpenAI()
    
    client = OpenAI(
        base_url=base_url,
        api_key= api_key,
    )
    return client


# ------------------------------------------------------------
# 1. Explanation for Readmission Prediction
# ------------------------------------------------------------

def explain_prediction(features: dict, probability: float, model: str = "gpt-4o-mini"):
    """
    Generate a clinician-facing explanation for the risk prediction.
    """
    client = get_llm()

    prompt = f"""
    You are a clinical assistant. A machine learning model predicted a
    readmission probability of {probability:.2f} for this patient.

    Patient features:
    {features}

    Provide a concise, clinically accurate explanation
    of WHY the model predicted this risk. Highlight the most important
    contributors and recommendations for clinicians.
    """

    response = client.chat.completions.create(
        model= model,
        messages=[{"role": "system", "content": "You are a helpful clinical AI assistant."},
                  {"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# ------------------------------------------------------------
# 2. Explain Drift Results
# ------------------------------------------------------------

def explain_drift(drift_json: dict):
    """
    Interpret drift statistics into human-readable summaries.
    """
    client = get_llm()

    prompt = f"""
    You are an MLOps assistant specializing in healthcare.
    Here is a drift report computed from KS-test and PSI:

    {drift_json}

    Explain in plain language:
    - Which features drifted the most
    - What the drift likely means
    - Whether this is dangerous for clinical accuracy
    - Recommended actions (validate data source, retrain model, etc.)
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are an MLOps drift analysis expert."},
                  {"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# ------------------------------------------------------------
# 3. Generate a Full Clinical Summary for Discharge Team
# ------------------------------------------------------------

def generate_clinical_summary(features: dict, probability: float):
    """
    Provide a short clinical summary for use in discharge planning.
    """
    client = get_llm()

    prompt = f"""
    Summarize this patient's readmission risk for a hospital discharge team.

    Patient features: {features}
    Predicted readmission probability: {probability:.2f}

    Include:
    - Key risk factors
    - Recommended follow-up interval
    - Suggested interventions to reduce readmission
    - Any safety flags the clinician should check
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a clinical risk communication expert."},
                  {"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# ------------------------------------------------------------
# 4. Safety Guardrails (LLM-assisted)
# ------------------------------------------------------------

def safety_guardrails(features: dict):
    """
    Identify abnormal, physiologically impossible, or clinically dangerous values.
    """
    client = get_llm()

    prompt = f"""
    Review these patient features for abnormal or clinically unsafe values:

    {features}

    Flag anything unrealistic or likely due to data entry error.
    Provide a brief explanation and recommended next action.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a clinical safety assistant."},
                  {"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
