# College Information Chatbot Web Application

A full-stack, offline-capable College Information Chatbot web application built with **Python, Flask, NLTK, SQLite, HTML5, CSS3, and JavaScript**.

---

## 🌟 Key Features

1. **Student Authentication & Security**:
   - Registration and Login with PBKDF2/Scrypt secure password hashing via `Werkzeug`.
   - Session management and instant redirect protection.
   - Clean logout functionality.

2. **NLP-Based Question Matching**:
   - Built using **NLTK** (tokenization, domain stop-words filtering, lemmatization via `WordNetLemmatizer`).
   - Dual-engine matching combining TF-IDF cosine similarity, n-grams, and domain token overlap boosting.
   - Conversational small-talk handler (greetings, introductions, helpful capabilities guidance, and goodbyes).
   - Polite fallback handling with admissions contact details when queries fall below confidence threshold.
   - **Zero paid APIs or external AI services** required.

3. **100+ FAQ Dataset (`questions.json`)**:
   - Contains **178 comprehensive FAQs** across 20+ categories:
     - Admissions, Cutoffs & Eligibility
     - Courses & Departments (CSE, AI/ML, ISE, ECE, Civil, Mech, MBA, MCA)
     - Fees, Installments & Refund Policies
     - State & Merit Scholarships (SSP, NSP, Pragati)
     - Examinations & VTU Academic Regulations (75% attendance rule, CGPA, backlogs, revaluation)
     - Placements, Highest Packages & Top Recruiters
     - Internships & Industry MoUs
     - Hostels, Mess Food, Timings & Security
     - Campus Facilities (Wi-Fi, Canteen, Medical, Labs, ATM, Parking)
     - Transport & Bus Routes
     - Central Library & Digital IEEE Resources
     - Student Clubs, Fests & Technical Societies
     - Sports, Gymnasium & Fitness
     - Anti-Ragging Policies & Student Redressal
     - Certificates, Bonafide Letters & Transcripts
   - Unknown college details are fully configurable in `questions.json` under `college_info`.

4. **Persistent Chat Memory**:
   - Every question and answer is automatically saved in SQLite (`college_chatbot.db`).
   - Chat history loads seamlessly across sessions for each student.
   - One-click **Clear Chat History** option with confirmation modal.

5. **Professional White & Blue UI**:
   - Deep royal blue (`#1e40af`, `#2563eb`) with crisp white surfaces and slate typography.
   - Responsive layout adapting smoothly to desktop, tablet, and mobile screens.
   - Collapsible navigation drawer on mobile devices.
   - Quick prompt suggestion chips and topic explorer.
   - Typing indicator animation and one-click message copy.

---

## 📁 Project Structure

```
College_Information_Chatbot/
│
├── app.py                     # Flask application routes, session handling & REST API
├── chatbot.py                 # NLP preprocessing, TF-IDF vectorization & response matching
├── database.py                # SQLite database management, hashing & chat history
├── questions.json             # 178 college FAQ questions, answers & configurable metadata
├── requirements.txt           # Python dependencies (Flask, nltk, scikit-learn, Werkzeug)
│
├── static/
│   ├── style.css              # Modern white & blue responsive stylesheet
│   └── script.js              # Chat interactions, asynchronous API fetch & UI animations
│
├── templates/
│   ├── index.html             # Main chatbot dashboard & message stream
│   ├── login.html             # Student login page
│   └── signup.html            # Student registration page
│
├── nltk_data/                 # Pre-bundled local NLTK tokenizers & corpora
└── college_chatbot.db         # SQLite database file (created automatically)
```

---

## 🚀 How to Run Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Flask Server
```bash
python app.py
```

### 3. Open in Browser
Visit:
```
http://127.0.0.1:5000
```
1. Click **Create your account** to register a student profile.
2. Log in and ask any question about the college!
