import google.generativeai as genai
from fuzzywuzzy import fuzz
import numpy as np

# ==========================
# 🔑 Configure API Key here
# ==========================
API_KEY = "AIzaSyA1SfGhreQD5nfRCyJez3Usu9-hBzELnrw"  # <-- replace with your API key
genai.configure(api_key=API_KEY)

# --------------------------
# Hard Match Scoring
# --------------------------
def hard_match_score(resume_text, keywords):
    score = 0
    for kw in keywords:
        if kw.lower().strip() in resume_text.lower():
            score += 1
    return (score / len(keywords)) * 50 if keywords else 0

# --------------------------
# Fuzzy Match Scoring
# --------------------------
def fuzzy_match_score(resume_text, jd_text):
    return fuzz.partial_ratio(resume_text.lower(), jd_text.lower()) / 2  # weighted out of 50

# --------------------------
# Semantic Match Scoring (Embeddings + fallback)
# --------------------------
def semantic_match_score(resume_text, jd_text):
    try:
        result_res = genai.embed_content(model="models/embedding-001", content=resume_text)
        result_jd = genai.embed_content(model="models/embedding-001", content=jd_text)
        res_emb = np.array(result_res["embedding"])
        jd_emb = np.array(result_jd["embedding"])
        cosine = np.dot(res_emb, jd_emb) / (np.linalg.norm(res_emb) * np.linalg.norm(jd_emb))
        return cosine * 100
    except Exception as e:
        print("⚠️ Semantic embeddings not available, using fuzzy similarity instead:", str(e))
        return fuzz.token_set_ratio(resume_text, jd_text)

# --------------------------
# Feedback Generation (Gemini)
# --------------------------
def generate_feedback(resume_text, jd_text):
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    prompt = f"""
    Resume: {resume_text[:2000]}
    Job Description: {jd_text[:2000]}

    Provide:
    1. Missing skills/certifications/projects.
    2. Verdict (High / Medium / Low suitability).
    3. 2-3 improvement suggestions.
    """
    try:
        response = model.generate_content(prompt)
        return response.text if response else "No feedback generated."
    except Exception as e:
        print("⚠️ Feedback generation failed:", str(e))
        return "No feedback generated due to quota/error."

# --------------------------
# Main Evaluation Function
# --------------------------
def evaluate_resume(resume_text, jd_text, keywords, strictness=70, model_choice="Fast Comparison Model"):
    hard = hard_match_score(resume_text, keywords)
    fuzzy = fuzzy_match_score(resume_text, jd_text)
    semantic = semantic_match_score(resume_text, jd_text)

    # Average of the three
    base_score = (hard + fuzzy + semantic) / 3

    # Apply strictness factor
    score = base_score * (strictness / 100)

    # Deep model boost if semantic alignment is strong
    if model_choice.startswith("Deep") and semantic > 70:
        score = min(100, score + 10)

    # Verdict thresholds
    if score >= 75:
        verdict = "High"
    elif score >= 50:
        verdict = "Medium"
    else:
        verdict = "Low"

    feedback = generate_feedback(resume_text, jd_text)

    return {
        "score": round(score, 2),
        "verdict": verdict,
        "feedback": feedback
    }
