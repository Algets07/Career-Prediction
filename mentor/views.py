import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.template.loader import get_template
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
import re
from .forms import CareerInputForm, SignupForm
from .ml.model import predict_top3, tiny_roadmap
from .models import Assessment
from .career_data import get_career_info


# -------------------------
# Public pages
# -------------------------
def home(request):
    return render(request, "mentor/home.html")


@login_required
def career_form(request):
    form = CareerInputForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        request.session["form_data"] = form.cleaned_data  # stash for predict
        return redirect("mentor:predict")
    return render(request, "mentor/form.html", {"form": form})


# -------------------------
# Prediction + save history
# -------------------------

@login_required
def predict(request):
    data = request.session.get("form_data")
    if not data:
        messages.warning(request, "Please fill the form first.")
        return redirect("mentor:career_form")

    # 1) Predict (each prob is 0..1 float)
    top3_raw = predict_top3(
        data["math"], data["science"], data["english"], data["arts"],
        data["coding"], data["design"], data["leadership"], data["communication"],
        data.get("interests", "")
    )

    # 2) Enrich for UI: convert prob to %, attach roadmap
    enriched = [(career, p * 100.0, tiny_roadmap(career)) for (career, p) in top3_raw]

    # 3) Career insights (salary/demand/courses) mapped by career name
    info_list = get_career_info([c for (c, _p, _rm) in enriched])
    info_map = {ci["name"]: ci for ci in info_list}

    # 4) Merge into card objects and sort by confidence desc
    cards = []
    for (career, prob_pct, roadmap) in enriched:
        cards.append({
            "career": career,
            "prob": float(prob_pct),           # percent for display
            "roadmap": roadmap,
            "info": info_map.get(career, {"name": career, "salary": "—", "demand": "—", "courses": []}),
        })
    cards.sort(key=lambda x: x["prob"], reverse=True)

    top_card = cards[0]
    other_cards = cards[1:]

    # 5) Save to DB: store probs as 0..1 JSON string
    top3_db = [{"career": c["career"], "prob": round(c["prob"] / 100.0, 6)} for c in cards]
    Assessment.objects.create(
        user=request.user,
        math=data["math"], science=data["science"], english=data["english"], arts=data["arts"],
        coding=data["coding"], design=data["design"], leadership=data["leadership"], communication=data["communication"],
        interests=data.get("interests", ""),
        top3=json.dumps(top3_db),
    )

    # 6) Render with top match separated
    return render(
        request,
        "mentor/result.html",
        {"top_card": top_card, "other_cards": other_cards}
    )
# -------------------------
# Auth
# -------------------------
def signup_view(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            messages.success(request, "Account created. Please log in.")
            return redirect("mentor:login")
    else:
        form = SignupForm()
    return render(request, "mentor/signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password"),
        )
        if user:
            login(request, user)
            return redirect("mentor:home")
        messages.error(request, "Invalid credentials.")
    return render(request, "mentor/login.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("mentor:home")


# -------------------------
# History
# -------------------------
@login_required

@login_required
def history_view(request):
    assessments = Assessment.objects.filter(user=request.user).order_by("-created_at")
    items = []
    for a in assessments:
        try:
            top3 = json.loads(a.top3) if a.top3 else []
        except Exception:
            top3 = []
        items.append({"obj": a, "top3": top3})
    return render(request, "mentor/history.html", {"items": items})



@login_required
def delete_history(request, pk=None):
    """Delete one assessment or all if pk is None."""
    if pk:
        # delete a single assessment
        try:
            item = Assessment.objects.get(pk=pk, user=request.user)
            item.delete()
        except Assessment.DoesNotExist:
            messages.error(request, "Record not found.")
    else:
        # delete all history for this user
        Assessment.objects.filter(user=request.user).delete()
    return redirect("mentor:history")



# -------------------------
# PDF Export (HTML -> PDF)
# -------------------------
@login_required
def export_pdf(request, pk: int):
    # Lazy import so migrations don't crash if the PDF lib is missing/pinned
    try:
        from xhtml2pdf import pisa
    except Exception as e:
        return HttpResponse(f"PDF engine not available: {e}", status=500)

    assessment = get_object_or_404(Assessment, pk=pk, user=request.user)

    # Parse stored JSON string
    try:
        parsed = json.loads(assessment.top3) if assessment.top3 else []
    except Exception:
        parsed = []

    # Build top3 with % for display
    top3 = [{"career": item["career"], "prob": float(item["prob"]) * 100.0} for item in parsed]

    # Career enrichment
    careers = [t["career"] for t in top3]
    career_info = get_career_info(careers)

    # Render HTML -> PDF
    template = get_template("mentor/report_pdf.html")
    html = template.render({"assessment": assessment, "top3": top3, "career_info": career_info})

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="career_report_{assessment.pk}.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response



@login_required
def chat_page(request):
    # Render the UI for the chatbot
    return render(request, "mentor/chat.html")

def _latest_assessment(user):
    try:
        return Assessment.objects.filter(user=user).order_by("-created_at").first()
    except Exception:
        return None

def _skill_hint(a):
    if not a:
        return ""
    scores = {
        "Math": a.math, "Science": a.science, "English": a.english, "Arts": a.arts,
        "Coding": a.coding, "Design": a.design, "Leadership": a.leadership, "Communication": a.communication,
    }
    top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:2]
    strong = ", ".join([f"{name} ({val:.0f})" for name, val in top])
    return f""

# map common user phrases → canonical career keys used by tiny_roadmap / careers.json
ALIAS = {
    "software engineer": "Software Engineer",
    "developer": "Software Engineer",
    "programmer": "Software Engineer",
    "data scientist": "Data Scientist",
    "ai engineer": "AI / ML Engineer",
    "ml engineer": "AI / ML Engineer",
    "machine learning engineer": "AI / ML Engineer",
    "cybersecurity": "Cybersecurity Specialist",
    "security engineer": "Cybersecurity Specialist",
    "cloud engineer": "Cloud Engineer",
    "devops": "Cloud Engineer",
    "ui/ux": "Designer / UI-UX",
    "ux designer": "Designer / UI-UX",
    "ui designer": "Designer / UI-UX",
    "designer": "Designer / UI-UX",
    "doctor": "Doctor / Healthcare",
    "healthcare": "Doctor / Healthcare",
    "lawyer": "Lawyer / Legal",
    "legal": "Lawyer / Legal",
    "entrepreneur": "Entrepreneur / Manager",
    "manager": "Entrepreneur / Manager",
    "teacher": "Teacher / Academic",
    "academic": "Teacher / Academic",
    "content creator": "Content Creator / Media",
    "media": "Content Creator / Media",
}

def _extract_careers(text):
    """Return list of canonical career names found in text."""
    text = text.lower()
    hits = []
    # check multi-word aliases first to avoid partial conflicts
    for k in sorted(ALIAS.keys(), key=len, reverse=True):
        if k in text:
            canon = ALIAS[k]
            if canon not in hits:
                hits.append(canon)
    return hits


# --- chatbot API ----------------------------------------------------------

@require_POST
@login_required
def chat_api(request):
    msg = (request.POST.get("message") or "").strip().lower()
    if not msg:
        return JsonResponse({"reply": "Please type a question about careers."})

    a = _latest_assessment(request.user)
    reply = None

    # 0) PROFESSIONAL ROADMAP INTENT  🔥
    # Triggers: "roadmap for X", "how to become X", "steps for X", "path to X"
    if (
        "roadmap" in msg or "how to become" in msg or "steps for" in msg
        or "path to" in msg or "career path for" in msg or "plan for" in msg
    ):
        targets = _extract_careers(msg)
        if not targets:
            reply = (
                "Tell me which role you want a roadmap for (e.g., "
                "'roadmap for data scientist' or 'steps for ui/ux designer')."
            )
        else:
            # If multiple mentioned, show the first; list others as suggestions
            primary = targets[0]
            steps = tiny_roadmap(primary)
            roadmap_txt = "\n".join([f"{i+1}. {s}" for i, s in enumerate(steps)])
            extra = ""
            if len(targets) > 1:
                extra = "\n\nAlso detected: " + ", ".join(targets[1:]) + \
                        ". Ask 'roadmap for <role>' to see those."
            reply = f"📍 Roadmap for **{primary}**:\n{roadmap_txt}{extra}{_skill_hint(a)}"
            return JsonResponse({"reply": reply})

    # 1) Salary insights
    if "salary" in msg or "pay" in msg or "package" in msg:
        targets = _extract_careers(msg) or ["Software Engineer", "Data Scientist", "Doctor / Healthcare"]
        info = get_career_info(targets)
        lines = [f"{ci['name']}: {ci.get('salary','—')}" for ci in info]
        reply = "Here are salary insights:\n" + "\n".join(lines) + _skill_hint(a) 
        
    elif "trending" in msg or "high demand" in msg or "popular" in msg or "in demand" in msg:
        reply = (
            "🚀 Careers in high demand right now:\n"
            "• Data Scientist / AI Engineer\n"
            "• Cybersecurity Specialist\n"
            "• Cloud Engineer\n"
            "• Doctor / Healthcare\n"
            "• UI/UX Designer"
            + _skill_hint(a)
        )       

    # 2) Course suggestions
    elif "course" in msg or "learn" in msg or "study" in msg or "syllabus" in msg:
        targets = _extract_careers(msg)
        if not targets:
            if "ui" in msg or "ux" in msg or "design" in msg:
                targets = ["Designer / UI-UX"]
            elif "data" in msg or "ml" in msg or "machine learning" in msg:
                targets = ["Data Scientist"]
            elif "software" in msg or "coding" in msg or "programming" in msg or "developer" in msg:
                targets = ["Software Engineer"]
            else:
                targets = ["Software Engineer", "Designer / UI-UX"]
        info = get_career_info(targets)
        parts = []
        for ci in info:
            crs = ci.get("courses") or []
            if crs:
                titles = ", ".join([c.get("title","") for c in crs])
                parts.append(f"{ci['name']}: {titles}")
        reply = ("You can explore:\n" + ("\n".join(parts) if parts else "No courses found.")) + _skill_hint(a)

    # 3) Trending / High demand

    elif "hi" in msg or "hai" in msg or "hello" in msg:
        reply =(
            "🌿 Welcome — I’m here to support your journey\n"
        )


    # 4) Government / Civil services
    elif "government" in msg or "civil services" in msg or "upsc" in msg or "psc" in msg:
        reply = (
            "🏛 Government job paths:\n"
            "• Civil Services (IAS, IPS, IFS)\n"
            "• PSU roles (engineers, management)\n"
            "• Teaching (UGC NET, schools)\n"
            "• Healthcare (doctors in govt hospitals)\n"
            "📚 Path: competitive exams like UPSC, SSC, state PSC, etc."
        )

    # 5) Short / quick courses
    elif "short course" in msg or "quick course" in msg or "certificate" in msg:
        reply = (
            "⏱ Short career-boosting courses:\n"
            "• Google Data Analytics (Coursera, ~6 months)\n"
            "• AWS Cloud Practitioner (Udemy, ~1 month)\n"
            "• Google UX Design (Coursera, ~4–6 months)\n"
            "• Digital Marketing Basics (edX, ~2 months)"
            + _skill_hint(a)
        )

    # 6) Future of AI jobs
    elif "future of ai" in msg or "ai jobs" in msg or "scope of ai" in msg:
        reply = (
            "🤖 Future AI career tracks:\n"
            "• AI Researcher (labs, academia)\n"
            "• ML Engineer (applied AI)\n"
            "• Robotics Engineer\n"
            "• AI Ethics & Policy roles\n"
            "Outlook: Very High demand in the next 5–10 years."
            + _skill_hint(a)
        )

    # 7) Comparisons
    elif "compare" in msg or ("vs" in msg and any(k in msg for k in ["data scientist","software engineer","ui/ux","lawyer","doctor","cloud","cybersecurity"])):
        reply = (
            "📊 Data Scientist vs Software Engineer:\n\n"
            "• Data Scientist → Focus on ML/AI, statistics, data storytelling.\n"
            "  Typical salary: ₹8L–₹30L (India), $100k–$200k (US)\n"
            "• Software Engineer → Build scalable apps, systems, tools.\n"
            "  Typical salary: ₹6L–₹24L (India), $80k–$180k (US)\n\n"
            "👉 Enjoy math/data/ML? Choose Data Scientist.\n"
            "👉 Enjoy building products/systems? Choose Software Engineer."
            + _skill_hint(a)
        )

    # 8) Careers by skills
    elif re.search(r"(job|career).*(math|statistics)", msg):
        reply = "Careers for strong math: Data Scientist, Quant Analyst, Engineer, Actuary." + _skill_hint(a)
    elif re.search(r"(job|career).*(design|ui|ux|creative)", msg):
        reply = "Design paths: UI/UX Designer, Product Designer, Motion Designer, Architect." + _skill_hint(a)
    elif re.search(r"(job|career).*(coding|programming|software|developer)", msg):
        reply = "Coding-heavy roles: Software Engineer, Backend/Frontend Dev, DevOps, Cloud Engineer." + _skill_hint(a)
    elif re.search(r"(job|career).*(communication|english|writing|public speaking)", msg):
        reply = "Strong communication fits: Product Manager, Marketing, PR, Teaching, Content Creator." + _skill_hint(a)
    elif re.search(r"(job|career).*(leadership|management)", msg):
        reply = "Leadership paths: Product Manager, Project Manager, Entrepreneur/Manager, Team Lead." + _skill_hint(a)

    # Fallback
    if not reply:
        reply = (
            "Asking about:\n"
            "• Roadmap (e.g., 'roadmap for data scientist', 'how to become a cloud engineer')\n"
            "• salary (e.g., 'Salary for Software Engineer')\n"
            "• Courses (e.g., 'Courses for UI/UX')\n"
            "• Trending careers (e.g., 'Which careers are in demand?')\n"
            "• Compare roles (e.g., 'Compare Data Scientist vs Software Engineer')\n"
            "• Careers for a skill (e.g., 'Jobs for strong math')."
            + _skill_hint(a)
        )

    return JsonResponse({"reply": reply})