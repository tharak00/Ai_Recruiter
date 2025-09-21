import streamlit as st
import sqlite3
import requests
from streamlit_lottie import st_lottie
from resume_parser import parse_resume
from evaluator import evaluate_resume

# -------------------------
# Page Config
# -------------------------
st.set_page_config(page_title="AI Recruiter", layout="wide")
st.title("🤖 AI Recruiter")

# -------------------------
# Custom CSS (Dark Gradient Theme)
# -------------------------
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #1f005c, #5b0060, #870160, #ac255e, #ca485c, #e16b5c, #f39060, #ffb56b);
        color: white;
    }
    h1, h2, h3, h4 {
        color: #FFD700;
    }
    .stMetric {
        background-color: #222;
        border-radius: 12px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------
# Lottie Loader
# -------------------------
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_resume = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_x62chJ.json")
if lottie_resume:
    st_lottie(lottie_resume, height=180, key="resume_anim")

# -------------------------
# Database setup
# -------------------------
DB_PATH = "resume_checker.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT,
    score REAL,
    verdict TEXT,
    feedback TEXT
)
""")
conn.commit()

# -------------------------
# Sidebar: JD Upload & Options
# -------------------------
st.sidebar.header("📌 Job Description & Settings")

jd_file = st.sidebar.file_uploader("Upload JD (PDF/DOCX)", type=["pdf", "docx"])
keywords = st.sidebar.text_area("Enter Must-Have Skills (comma separated):", "Python, Machine Learning, SQL")

strictness = st.sidebar.slider("Skill Matching Strictness", 0, 100, 70)
model_choice = st.sidebar.selectbox(
    "Text Comparison Model",
    ["Fast Comparison Model (quick, less detailed)", "Deep Comparison Model (slower, more accurate)"]
)

# -------------------------
# Process JD & Resumes
# -------------------------
if jd_file:
    jd_text = parse_resume(jd_file)

    st.subheader("📄 Job Description")
    st.write(jd_text[:1000] + "..." if len(jd_text) > 1000 else jd_text)

    st.header("📤 Upload Resumes")
    resume_files = st.file_uploader("Upload resumes", type=["pdf", "docx"], accept_multiple_files=True)

    if resume_files:
        results = []
        for res in resume_files:
            resume_text = parse_resume(res)
            result = evaluate_resume(
                resume_text,
                jd_text,
                keywords.split(","),
                strictness,
                model_choice
            )
            results.append({"Name": res.name, **result})

            cursor.execute(
                "INSERT INTO evaluations (file_name, score, verdict, feedback) VALUES (?, ?, ?, ?)",
                (res.name, result["score"], result["verdict"], result["feedback"])
            )
            conn.commit()

        # -------------------------
        # Display results
        # -------------------------
        st.subheader("✨ Evaluation Results ✨")
        for r in results:
            st.markdown(f"## 📄 {r['Name']}")
            st.progress(int(r['score']))
            st.metric(label="Relevance Score", value=f"{r['score']} / 100")
            verdict_icon = "✅ Relevant" if r["verdict"].lower() == "relevant" else "❌ Not Relevant"
            st.write(f"**Verdict:** {verdict_icon}")
            st.info(r['feedback'])
            st.markdown("---")

# -------------------------
# Sidebar: View past evaluations
# -------------------------
st.sidebar.header("📂 Past Evaluations")
if st.sidebar.button("Show All Stored Evaluations"):
    cursor.execute("SELECT * FROM evaluations ORDER BY id DESC")
    rows = cursor.fetchall()
    st.subheader("📂 Stored Evaluation Results")
    for r in rows:
        st.markdown(f"### 📄 {r[1]}")
        st.progress(int(r[2]))
        st.write(f"**Score:** {r[2]} / 100 🏅")
        st.write(f"**Verdict:** {r[3]} {'✅' if r[3].lower() == 'relevant' else '❌'}")
        st.write("**Feedback:** 📝")
        st.write(r[4])
        st.markdown("---")

# -------------------------
# Sidebar: Show Shortlisted Candidates
# -------------------------
st.sidebar.header("🏆 Shortlisted Candidates (Score ≥ 70)")
if st.sidebar.button("Show Shortlisted"):
    cursor.execute("SELECT * FROM evaluations WHERE score >= 70 ORDER BY score DESC")
    shortlisted = cursor.fetchall()
    st.subheader("🏆 Shortlisted Candidates")
    if shortlisted:
        for r in shortlisted:
            st.markdown("🎉 **Shortlisted!** 🎉")
            st.markdown(f"### 📄 {r[1]}")
            st.progress(int(r[2]))
            st.write(f"**Score:** {r[2]} / 100")
            st.write(f"**Verdict:** {r[3]}")
            st.success(r[4])
            st.markdown("---")
    else:
        st.write("No candidates have score ≥ 70 yet.")

