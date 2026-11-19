import json
import os
import re
import string
import nltk

# Configure local NLTK data directory inside workspace
workspace_nltk_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nltk_data")
if workspace_nltk_data not in nltk.data.path:
    nltk.data.path.insert(0, workspace_nltk_data)

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class CollegeChatbot:
    def __init__(self, json_path=None):
        if json_path is None:
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "questions.json")
        self.json_path = json_path
        
        self.lemmatizer = WordNetLemmatizer()
        
        # Standard English stopwords
        try:
            self.stop_words = set(stopwords.words('english'))
        except Exception:
            self.stop_words = {
                'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're",
                "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he',
                'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's",
                'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
                'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are',
                'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do',
                'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because',
                'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
                'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
                'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
                'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
                'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
                'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will',
                'just', 'don', 'should', "should've", 'now'
            }
            
        # College and education domain keywords we should never filter out
        domain_keywords = {
            'fee', 'fees', 'hostel', 'bus', 'ssp', 'nsp', 'exam', 'exams', 'vtu',
            'attendance', 'placements', 'placement', 'gym', 'gymnasium', 'canteen', 'library',
            'admission', 'admissions', 'scholarship', 'scholarships', 'sports',
            'course', 'courses', 'branch', 'branches', 'cutoff', 'rank', 'salary',
            'package', 'internship', 'internships', 'mess', 'wifi', 'leave',
            'principal', 'ragging', 'bonafide', 'transcript', 'lor', 'contact'
        }
        # Generic terms that appear in almost all questions and should not bias category matches
        generic_terms = {'college', 'institute', 'institution', 'university', 'campus', 'student', 'students'}
        self.stop_words = (self.stop_words - domain_keywords) | generic_terms
        
        self.college_info = {}
        self.faqs = []
        self.categories = set()
        
        # Training corpus structures
        self.corpus_texts = []
        self.corpus_faq_indices = []
        self.vectorizer = None
        self.tfidf_matrix = None
        
        self.load_data()
        self.train_vectorizer()

    def preprocess(self, text):
        if not text:
            return ""
        text = text.lower()
        
        # Domain abbreviations & synonyms mapping
        synonyms = {
            r'\bgym\b': 'gymnasium gym',
            r'\bfees\b': 'fee',
            r'\bbe\b': 'btech engineering be',
            r'\bb\.tech\b': 'btech engineering',
            r'\bbtech\b': 'btech engineering',
            r'\bm\.tech\b': 'mtech engineering',
            r'\bmtech\b': 'mtech engineering',
            r'\bprof\b': 'professor',
            r'\bdept\b': 'department',
            r'\badmin\b': 'administrative administration',
            r'\battendence\b': 'attendance',
            r'\bcgpa\b': 'cgpa grade grading',
            r'\bsgpa\b': 'sgpa grade grading',
            r'\blor\b': 'letter recommendation lor',
            r'\bnoc\b': 'noc permission certificate'
        }
        for pattern, replacement in synonyms.items():
            text = re.sub(pattern, replacement, text)

        # Replace punctuation with spaces
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        
        try:
            tokens = word_tokenize(text)
        except Exception:
            tokens = text.split()
            
        lemmatized_tokens = []
        for word in tokens:
            if word not in self.stop_words and len(word) > 1:
                try:
                    lemma = self.lemmatizer.lemmatize(word, pos='v')
                    lemma = self.lemmatizer.lemmatize(lemma, pos='n')
                except Exception:
                    lemma = word
                lemmatized_tokens.append(lemma)
                
        return " ".join(lemmatized_tokens)

    def load_data(self):
        if not os.path.exists(self.json_path):
            raise FileNotFoundError(f"Questions file not found at {self.json_path}")
            
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.college_info = data.get("college_info", {})
        raw_faqs = data.get("faqs", [])
        
        self.faqs = []
        for faq in raw_faqs:
            answer = faq.get("answer", "")
            try:
                formatted_answer = answer.format(**self.college_info)
            except Exception:
                formatted_answer = answer
                
            self.faqs.append({
                "id": faq.get("id"),
                "category": faq.get("category", "General"),
                "patterns": faq.get("patterns", []),
                "answer": formatted_answer
            })
            self.categories.add(faq.get("category", "General"))

    def train_vectorizer(self):
        self.corpus_texts = []
        self.corpus_faq_indices = []
        
        for idx, faq in enumerate(self.faqs):
            # Index all patterns for each FAQ item
            for pattern in faq["patterns"]:
                cleaned = self.preprocess(pattern)
                if cleaned:
                    self.corpus_texts.append(cleaned)
                    self.corpus_faq_indices.append(idx)
                    
            # Index combined answer and category keywords
            ans_snippet = self.preprocess(faq.get("answer", "")[:150])
            cat_cleaned = self.preprocess(faq.get("category", ""))
            combined = f"{cat_cleaned} {ans_snippet}".strip()
            if combined:
                self.corpus_texts.append(combined)
                self.corpus_faq_indices.append(idx)

        # Build TF-IDF model
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus_texts)

    def check_small_talk(self, query):
        clean_q = re.sub(r'[^a-z0-9\s]', '', query.lower()).strip()
        tokens = set(clean_q.split())
        
        # Greetings check
        greeting_words = {'hi', 'hello', 'hey', 'greetings', 'morning', 'afternoon', 'evening', 'hola', 'namaste'}
        if clean_q in greeting_words or (len(tokens) <= 3 and any(w in greeting_words for w in tokens)):
            college_name = self.college_info.get("name", "our college")
            return (
                f"Hello! 👋 Welcome to the **{college_name} Virtual Helpdesk**.\n\n"
                "I can assist you with:\n"
                "• 🎓 **Admissions & Cutoffs** (KCET, COMEDK, Management)\n"
                "• 📚 **Degree Courses & Eligibility**\n"
                "• 💰 **Fee Structure & Scholarships** (SSP, Merit, Pragati)\n"
                "• 💼 **Placements & Internships** (Companies, Packages)\n"
                "• 🏢 **Hostels, Food & Transport**\n"
                "• 📝 **VTU Exams & Attendance Rules**\n\n"
                "How can I help you today?"
            )
            
        how_are_you_phrases = ['how are you', 'how are you doing', 'hows it going', 'how do you do']
        if any(p in clean_q for p in how_are_you_phrases):
            return "I'm running great and ready to assist you! What college information can I find for you today?"
            
        who_are_you_phrases = ['who are you', 'what is your name', 'what are you', 'tell me about yourself']
        if any(p in clean_q for p in who_are_you_phrases):
            college_name = self.college_info.get("name", "our college")
            return (
                f"I am the official **College Information Assistant** for {college_name}. "
                "I am built using Python, Flask, and NLTK to answer student queries about admissions, "
                "academics, campus facilities, exams, and career placements 24/7."
            )
            
        capabilities_phrases = ['what can you do', 'help', 'menu', 'options', 'features', 'what can i ask']
        if clean_q in capabilities_phrases:
            return (
                "Here are key topics you can ask me about:\n"
                "• 🎓 **Admissions**: Eligibility, KCET/COMEDK cutoffs, documents required, application deadlines\n"
                "• 📚 **Courses**: B.Tech branches (CSE, AI/ML, ISE, ECE, Civil), MBA, MCA, syllabus\n"
                "• 💰 **Fees & Scholarships**: Annual tuition, installments, SSP/NSP scholarships\n"
                "• 💼 **Placements**: Recruiters, packages, eligibility, internship policies\n"
                "• 🏢 **Hostels & Transport**: Room facilities, mess food, bus routes and fees\n"
                "• 📝 **Exams**: Attendance criteria (75%), VTU grading, backlogs, revaluations\n"
                "Feel free to type your question!"
            )
            
        thanks_words = {'thanks', 'thank', 'thx', 'appreciate'}
        if any(w in tokens for w in thanks_words):
            return "You're very welcome! If you have any more questions about the college, feel free to ask anytime. Have a wonderful day! 😊"
            
        bye_words = {'bye', 'goodbye', 'cya', 'farewell'}
        if any(w in tokens for w in bye_words):
            return "Goodbye! Best wishes for your academic goals. Feel free to come back whenever you need assistance! 🎓"
            
        return None

    def get_response(self, user_query):
        if not user_query or not user_query.strip():
            return {
                "answer": "Please enter a question so I can assist you.",
                "confidence": 0.0,
                "category": None
            }
            
        raw_query = user_query.strip()
        
        # 1. Check small talk
        small_talk = self.check_small_talk(raw_query)
        if small_talk:
            return {
                "answer": small_talk,
                "confidence": 1.0,
                "category": "Small Talk"
            }
            
        # 2. Preprocess with NLTK
        processed_query = self.preprocess(raw_query)
        if not processed_query:
            return self.get_fallback_response()
            
        # 3. Vectorize and compute similarity
        query_vector = self.vectorizer.transform([processed_query])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]
        
        faq_scores = {}
        query_tokens = set(processed_query.split())
        
        for idx, score in enumerate(similarities):
            faq_idx = self.corpus_faq_indices[idx]
            if faq_idx not in faq_scores or score > faq_scores[faq_idx]:
                faq_scores[faq_idx] = score
                
        # Keyword and domain overlap boosting
        for faq_idx, score in faq_scores.items():
            faq_item = self.faqs[faq_idx]
            
            # Check pattern overlap
            for pattern in faq_item["patterns"]:
                p_clean = self.preprocess(pattern)
                p_tokens = set(p_clean.split())
                if p_tokens and query_tokens:
                    overlap = len(query_tokens.intersection(p_tokens))
                    if overlap > 0:
                        # Add bonus proportional to token match ratio
                        ratio = overlap / len(query_tokens)
                        faq_scores[faq_idx] += (ratio * 0.25)
                        
            # Exact phrase match in pattern bonus
            for pattern in faq_item["patterns"]:
                if pattern.lower() in raw_query.lower() or raw_query.lower() in pattern.lower():
                    faq_scores[faq_idx] += 0.35
                    
        sorted_candidates = sorted(faq_scores.items(), key=lambda x: x[1], reverse=True)
        
        if not sorted_candidates:
            return self.get_fallback_response(query_tokens)
            
        best_idx, best_score = sorted_candidates[0]
        
        CONFIDENCE_THRESHOLD = 0.18
        if best_score < CONFIDENCE_THRESHOLD:
            return self.get_fallback_response(query_tokens)
            
        matched_faq = self.faqs[best_idx]
        
        return {
            "answer": matched_faq["answer"],
            "confidence": round(float(best_score), 3),
            "category": matched_faq["category"],
            "id": matched_faq["id"]
        }

    def get_fallback_response(self, query_tokens=None):
        college_name = self.college_info.get("name", "our college")
        contact_email = self.college_info.get("contact_email", "the college office")
        phone = self.college_info.get("phone", "the helpline")
        
        suggestions = [
            "What courses and B.Tech branches are offered?",
            "What is the eligibility for admission?",
            "What is the placement record and top companies?",
            "What are the hostel facilities and fees?",
            "What is the minimum attendance requirement for VTU exams?",
            "How can I apply for SSP scholarship?"
        ]
        
        text = (
            f"I'm sorry, I could not find a specific match for that question in the college FAQ database.\n\n"
            f"For direct guidance regarding {college_name}, please reach out to the college office:\n"
            f"• 📞 **Helpline**: {phone}\n"
            f"• ✉️ **Email**: {contact_email}\n\n"
            f"💡 **Common questions you can ask me:**\n" + "\n".join([f"• {s}" for s in suggestions])
        )
        return {
            "answer": text,
            "confidence": 0.0,
            "category": "Unknown",
            "is_fallback": True
        }

    def get_quick_suggestions(self):
        categorized = {}
        for faq in self.faqs:
            cat = faq["category"]
            if cat not in categorized:
                categorized[cat] = []
            if len(categorized[cat]) < 2 and faq["patterns"]:
                categorized[cat].append(faq["patterns"][0])
        return categorized

    def get_college_info(self):
        return self.college_info

_chatbot_instance = None

def get_chatbot():
    global _chatbot_instance
    if _chatbot_instance is None:
        _chatbot_instance = CollegeChatbot()
    return _chatbot_instance

if __name__ == "__main__":
    bot = CollegeChatbot()
    print("Testing chatbot queries:\n")
    test_queries = [
        "Hi there",
        "Where is the college located?",
        "What is the admission process for B.Tech?",
        "What are the top recruiters in placements?",
        "What are the hostel timings?",
        "How much attendance is needed to write VTU exams?",
        "How can I apply for SSP scholarship?",
        "Is there a gym in college?",
        "Can I get a bonafide certificate?"
    ]
    for q in test_queries:
        res = bot.get_response(q)
        print(f"Q: {q}")
        print(f"Category: {res.get('category')} (Confidence: {res.get('confidence')})")
        print(f"A: {res['answer'][:120]}...\n")
