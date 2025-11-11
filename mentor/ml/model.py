from __future__ import annotations
from pathlib import Path
from typing import List, Tuple, Dict
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from joblib import dump, load

# -------------------------
# Paths / Artifacts
# -------------------------
BASE_DIR = Path(__file__).resolve().parent
ART_DIR = BASE_DIR / "artifacts"
ART_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = ART_DIR / "model.joblib"

# -------------------------
# Labels / Interests
# -------------------------
CAREERS: List[str] = [
    "Software Engineer",
    "Data Scientist",
    "Doctor / Healthcare",
    "Lawyer / Legal",
    "Designer / UI-UX",
    "Entrepreneur / Manager",
    "Teacher / Academic",
    "Content Creator / Media",
]

# Per-career keywords (used for post-probability boost)
INTEREST_KEYWORDS: Dict[str, List[str]] = {
    "Software Engineer": ["code","coding","software","apps","web","robot","program","ml","ai","backend","frontend"],
    "Data Scientist": ["data","stats","statistics","analytics","machine learning","ml","ai","research","pandas","kaggle"],
    "Doctor / Healthcare": ["bio","biology","medicine","health","care","doctor","hospital","clinic"],
    "Lawyer / Legal": ["law","legal","justice","rights","policy","court","litigation","contract"],
    "Designer / UI-UX": ["design","ui","ux","graphic","art","creative","illustration","figma","wireframe"],
    "Entrepreneur / Manager": ["startup","business","entrepreneur","management","team","lead","pitch","mvp","marketing"],
    "Teacher / Academic": ["teach","mentor","training","education","academy","learn","lesson","syllabus"],
    "Content Creator / Media": ["content","writer","blog","video","media","social","story","editor","script"],
}

# -------------------------
# Training data synthesis
# -------------------------
def _rng():
    return np.random.default_rng(7)

def _make_samples_for(career: str, n: int = 140):
    """Make synthetic training samples around a hand-crafted mean profile."""
    bases = {
        "Software Engineer":      [85, 75, 60, 40, 90, 45, 55, 60, 15],
        "Data Scientist":         [88, 80, 65, 45, 75, 45, 55, 65, 15],
        "Doctor / Healthcare":    [60, 92, 75, 45, 20, 40, 65, 70, 15],
        "Lawyer / Legal":         [55, 55, 90, 55, 25, 45, 75, 85, 15],
        "Designer / UI-UX":       [45, 45, 70, 90, 35, 92, 55, 70, 15],
        "Entrepreneur / Manager": [65, 55, 75, 60, 45, 55, 92, 85, 15],
        "Teacher / Academic":     [60, 60, 92, 55, 35, 45, 75, 85, 15],
        "Content Creator / Media":[45, 45, 85, 75, 35, 70, 65, 92, 15],
    }
    mean = bases[career]
    cov = np.diag([80, 80, 80, 80, 90, 90, 80, 80, 30])  # noise per feature
    X = _rng().multivariate_normal(mean, cov, size=n).clip(0, 100)
    y = np.full((n,), CAREERS.index(career), dtype=int)
    return X, y

def train_if_missing() -> None:
    if MODEL_PATH.exists():
        return
    Xs, ys = [], []
    for c in CAREERS:
        Xc, yc = _make_samples_for(c, 140)
        Xs.append(Xc)
        ys.append(yc)
    X = np.vstack(Xs)
    y = np.concatenate(ys)

    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=250, multi_class="multinomial"))
    ])
    model.fit(X, y)
    dump(model, MODEL_PATH)

def load_model() -> Pipeline:
    train_if_missing()
    return load(MODEL_PATH)

# -------------------------
# Interest → per-career boost
# -------------------------
def interest_scores_by_career(interests: str) -> Dict[str, float]:
    """
    Compute a lightweight per-career score in [0, 1] by counting keyword hits.
    """
    text = (interests or "").lower()
    scores: Dict[str, float] = {}
    for career, kws in INTEREST_KEYWORDS.items():
        hits = sum(1 for k in kws if k in text)
        # scale: 0 hits -> 0.0, 1 hit -> 0.3, 2 -> 0.6, 3+ -> 1.0
        if hits <= 0:
            s = 0.0
        elif hits == 1:
            s = 0.3
        elif hits == 2:
            s = 0.6
        else:
            s = 1.0
        scores[career] = s
    return scores

def _clip01(x: float) -> float:
    return float(min(100.0, max(0.0, x)))

# -------------------------
# Public API
# -------------------------
def predict_top3(
    math, science, english, arts, coding, design, leadership, communication, interests
) -> List[Tuple[str, float]]:
    """
    Returns top-3 (career, probability) with interest-aware boosting.
    Probabilities are re-normalized to sum to 1 after boosting.
    """
    model = load_model()

    # Defensive clipping to 0–100
    vec = np.array([
        _clip01(float(math)),
        _clip01(float(science)),
        _clip01(float(english)),
        _clip01(float(arts)),
        _clip01(float(coding)),
        _clip01(float(design)),
        _clip01(float(leadership)),
        _clip01(float(communication)),
        15.0,  # keep the 9th feature at the training baseline (stable)
    ], dtype=float).reshape(1, -1)

    probs = model.predict_proba(vec)[0]  # base probs from model

    # Per-career interest boost (post-proc), then renormalize
    scores = interest_scores_by_career(interests)
    alpha = 0.20  # up to +20% multiplicative boost for strong interest alignment
    boosts = np.array([1.0 + alpha * scores[c] for c in CAREERS], dtype=float)
    boosted = probs * boosts
    if boosted.sum() > 0:
        boosted = boosted / boosted.sum()

    idx = np.argsort(boosted)[::-1][:3]
    return [(CAREERS[i], float(boosted[i])) for i in idx]

def tiny_roadmap(career: str) -> List[str]:
    maps: Dict[str, List[str]] = {
        "Software Engineer": [
            "📘 Master DSA, OOP, and problem-solving (LeetCode/HackerRank)",
            "💻 Build 3–5 projects (web/mobile/systems) with clean code",
            "🛠 Git/GitHub, SQL/NoSQL, REST; one cloud (AWS/GCP/Azure)",
            "⚙️ Basics of CI/CD, Docker; dip toes into Kubernetes",
            "🚀 Internships, open-source; refine resume & LinkedIn"
        ],
        "Data Scientist": [
            "📘 Stats/probability/linear-algebra + Python/R",
            "📊 EDA & feature engineering (pandas/matplotlib)",
            "🤖 ML (scikit-learn/XGBoost) → DL (PyTorch/TensorFlow)",
            "🧠 2–3 domain projects (NLP/CV/time-series) with clear impact",
            "📂 Kaggle/portfolio; communicate results & trade-offs"
        ],
        "Doctor / Healthcare": [
            "📘 Bio/Chem foundations; entrance prep",
            "🧪 Shadow/volunteer in clinics; basic patient comms",
            "💡 Explore telemedicine & AI-assisted diagnostics",
            "📚 Shortlist specializations; plan study timeline",
            "🚀 Contribute to case studies or public health projects"
        ],
        "Lawyer / Legal": [
            "📘 Legal writing & case-briefing drills",
            "🗣 Debates/MUN; articulation & reasoning",
            "🖥 Intro to cyber/IP law and tech contracts",
            "📂 1–2 internships; pro bono or clinic work",
            "🚀 Build a writing portfolio (notes/blogs)"
        ],
        "Designer / UI-UX": [
            "🎨 Typography/color/design systems fundamentals",
            "🛠 Figma (auto-layout, components, prototypes)",
            "📱 Redesign 3–4 apps/sites; write case studies",
            "♿ Accessibility & usability testing basics",
            "📂 Portfolio site + Behance/Dribbble presence"
        ],
        "Entrepreneur / Manager": [
            "💡 Validate 1–2 ideas with 10–20 real users",
            "📊 Learn finance/marketing/product strategy basics",
            "🛠 Build an MVP (no-code OK); measure usage",
            "🤝 Join incubator/mentors; iterate pitch",
            "🌍 Plan hiring/ops; document processes early"
        ],
        "Teacher / Academic": [
            "📘 Subject depth + pedagogy basics",
            "🧪 Design 5 lesson plans with outcomes",
            "🎥 Record micro-lessons; collect feedback",
            "🧑‍🏫 Tutor/TA experience; assessment design",
            "📂 Share notes/videos; build a teacher brand"
        ],
        "Content Creator / Media": [
            "🎯 Pick a niche; publish 2×/week",
            "🎬 Storytelling/editing; hook-based scripting",
            "🧰 Learn analytics & thumbnail/caption craft",
            "🤝 Collaborate with 3 creators; cross-promote",
            "💰 Map monetization (sponsorships/affiliates)"
        ],
    }
    return maps.get(career, [
        "📘 Strengthen fundamentals",
        "💡 Build small projects and ship",
        "🤝 Network & seek mentors"
    ])
