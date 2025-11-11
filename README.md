# 🎯 Career Prediction and Mentor Recommendation System

An **AI-powered web application** that predicts the most suitable career paths for students based on their **skills, interests, and academic background**.  
The system also recommends **mentors, courses, and learning resources** to help users grow in their chosen domain.

---

## 🚀 Features

- 🧠 **Career Prediction:** Predicts top 3 career paths using Machine Learning and skill-based analysis.  
- 👨‍🏫 **Mentor Recommendation:** Suggests mentors or experts from relevant fields.  
- 📚 **Course Suggestion:** Links suitable online courses (Coursera, Udemy, etc.) to improve skills.  
- 👤 **User Dashboard:** Personalized dashboard to view predictions, mentors, and progress.  
- 🗂️ **Admin Panel:** Manage users, datasets, and model updates.  
- 🌐 **Web-Based Interface:** Developed using Django framework for seamless interaction.  

---

## 🧩 Tech Stack

| Component | Technology Used |
|------------|----------------|
| **Frontend** | HTML5, CSS3, Bootstrap, JavaScript |
| **Backend** | Python, Django |
| **Machine Learning** | Scikit-learn, Pandas, NumPy |
| **Database** | SQLite / MySQL |
| **Version Control** | Git, GitHub |
| **Deployment (optional)** | Render / Heroku / Vercel |

---

## 🧠 Machine Learning Model

- **Dataset:** Skill–Career dataset (custom or public career dataset)
- **Preprocessing:** Label Encoding, Data Cleaning, Feature Scaling  
- **Model Used:** Random Forest / Decision Tree / SVM / Hybrid Recommendation Model  
- **Output:** Top 3 predicted career domains based on input parameters.  

---

## ⚙️ Installation & Setup

```bash
# 1️⃣ Clone the repository
git clone https://github.com/Algets07/Career-Prediction.git

# 2️⃣ Navigate to project directory
cd Career-Prediction

# 3️⃣ Create and activate virtual environment
python -m venv venv
venv\Scripts\activate   # (for Windows)
source venv/bin/activate  # (for Linux/Mac)

# 4️⃣ Install dependencies
pip install -r requirements.txt

# 5️⃣ Run database migrations
python manage.py migrate

# 6️⃣ Start the development server
python manage.py runserver
