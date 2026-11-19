import unittest
import json
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from chatbot import get_chatbot
from app import app

class CollegeChatbotTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()
        database.init_db()
        cls.chatbot = get_chatbot()

    def test_01_database_user_registration_and_auth(self):
        print("\n[TEST] 1. Testing user registration and secure password hashing...")
        import uuid
        uname = f"test_{uuid.uuid4().hex[:6]}"
        email = f"{uname}@example.com"
        password = "SecurePassword123!"
        
        # Register user
        success, user_data = database.register_user(uname, email, password, "Test Student", "CSE")
        self.assertTrue(success, f"Registration failed: {user_data}")
        self.assertEqual(user_data["username"], uname)
        
        # Test duplicate registration
        dup_success, dup_msg = database.register_user(uname, email, password, "Test Student", "CSE")
        self.assertFalse(dup_success)
        self.assertIn("already registered", dup_msg.lower())
        
        # Test successful authentication by username
        auth_success, auth_user = database.authenticate_user(uname, password)
        self.assertTrue(auth_success)
        self.assertEqual(auth_user["email"], email)
        
        # Test successful authentication by email
        auth_email_success, auth_user_2 = database.authenticate_user(email, password)
        self.assertTrue(auth_email_success)
        self.assertEqual(auth_user_2["username"], uname)
        
        # Test wrong password
        fail_auth, fail_msg = database.authenticate_user(uname, "WrongPassword")
        self.assertFalse(fail_auth)
        print("  -> User registration & hashed password verification passed.")

    def test_02_database_chat_history(self):
        print("\n[TEST] 2. Testing SQLite chat history save, fetch & clear...")
        import uuid
        uname = f"hist_{uuid.uuid4().hex[:6]}"
        _, user = database.register_user(uname, f"{uname}@example.com", "Password123!", "History Student")
        user_id = user["id"]
        
        # Save messages
        msg1_id, t1 = database.save_chat_message(user_id, "user", "What are the college fees?")
        msg2_id, t2 = database.save_chat_message(user_id, "bot", "College fees vary according to quota...")
        
        # Retrieve history
        history = database.get_chat_history(user_id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["sender"], "user")
        self.assertEqual(history[0]["message"], "What are the college fees?")
        self.assertEqual(history[1]["sender"], "bot")
        
        # Clear history
        database.clear_chat_history(user_id)
        cleared_history = database.get_chat_history(user_id)
        self.assertEqual(len(cleared_history), 0)
        print("  -> Chat history operations passed.")

    def test_03_questions_json_count_and_content(self):
        print("\n[TEST] 3. Testing questions.json size and college_info schema...")
        with open("questions.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.assertIn("college_info", data)
        self.assertIn("faqs", data)
        faq_count = len(data["faqs"])
        print(f"  -> Total FAQs loaded: {faq_count}")
        self.assertGreaterEqual(faq_count, 100, "Must have 100+ college FAQs!")
        
        # Check that unknown college details are configurable
        info = data["college_info"]
        self.assertIn("name", info)
        self.assertIn("affiliation", info)
        self.assertIn("phone", info)
        self.assertIn("contact_email", info)

    def test_04_nlp_chatbot_matching(self):
        print("\n[TEST] 4. Testing NLP response matching across multiple domains...")
        queries = [
            ("Where is the campus located?", "General Information"),
            ("What are the undergraduate B.Tech courses offered?", "Courses & Academics"),
            ("What is the B.E. admission process and eligibility?", "Admissions"),
            ("What is the average and highest placement package?", "Placements & Training"),
            ("Who are the top recruiting companies visiting the campus?", "Placements & Training"),
            ("What are the hostel room facilities and mess food?", "Hostel & Living"),
            ("What is the minimum attendance required for VTU examinations?", "Exams & Academics"),
            ("How do I apply for the SSP scholarship in Karnataka?", "Scholarships"),
            ("Which routes do the college buses travel?", "Transport"),
            ("What are the library borrowing limits and timings?", "Library"),
            ("Is there a gym or sports grounds available on campus?", "Sports & Fitness"),
            ("How can I get a Bonafide Certificate?", "Student Services"),
            ("What is the anti-ragging policy?", "Discipline & Safety")
        ]
        
        for q, expected_cat in queries:
            res = self.chatbot.get_response(q)
            self.assertIsNotNone(res["answer"])
            self.assertGreater(len(res["answer"]), 20)
            self.assertIn(res["category"], [expected_cat, "General Information", "Campus Facilities", "Admissions"])
            print(f"  ✓ Query: '{q}' -> Matched: [{res['category']}] (Score: {res['confidence']})")

    def test_05_flask_routes_and_api(self):
        print("\n[TEST] 5. Testing Flask routes, sessions, and REST endpoints...")
        
        # 1. GET /login returns 200
        res = self.client.get("/login")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Student Portal Login", res.data)
        
        # 2. GET /signup returns 200
        res = self.client.get("/signup")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Create Student Account", res.data)
        
        # 3. POST /signup registers and logs in
        import uuid
        uname = f"flask_{uuid.uuid4().hex[:6]}"
        signup_res = self.client.post("/signup", data={
            "full_name": "Flask Tester",
            "username": uname,
            "email": f"{uname}@example.com",
            "department": "Computer Science & Engineering",
            "password": "Password123!",
            "confirm_password": "Password123!"
        }, follow_redirects=True)
        self.assertEqual(signup_res.status_code, 200)
        self.assertIn(b"Virtual Advisor", signup_res.data)
        
        # 4. POST /api/chat as logged-in student
        chat_res = self.client.post("/api/chat", json={
            "message": "What is the placement record of the college?"
        })
        self.assertEqual(chat_res.status_code, 200)
        chat_data = json.loads(chat_res.data)
        self.assertEqual(chat_data["status"], "success")
        self.assertIn("reply", chat_data)
        print(f"  ✓ Chat API response: {chat_data['reply'][:90]}...")
        
        # 5. GET /api/history returns the conversation
        hist_res = self.client.get("/api/history")
        self.assertEqual(hist_res.status_code, 200)
        hist_data = json.loads(hist_res.data)
        self.assertEqual(len(hist_data["history"]), 2) # user query + bot response
        
        # 6. POST /api/history/clear clears the history
        clear_res = self.client.post("/api/history/clear")
        self.assertEqual(clear_res.status_code, 200)
        
        hist_res2 = self.client.get("/api/history")
        hist_data2 = json.loads(hist_res2.data)
        self.assertEqual(len(hist_data2["history"]), 0)
        
        # 7. GET /logout logs out student
        logout_res = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(logout_res.status_code, 200)
        self.assertIn(b"Student Portal Login", logout_res.data)
        print("  -> All Flask routes and API tests passed successfully.")

if __name__ == "__main__":
    unittest.main()
