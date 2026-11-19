import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import database
from chatbot import get_chatbot

app = Flask(__name__)
# Generate or use a session secret key
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "college_chatbot_secret_key_2026_tjit")
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Ensure database is initialized at app startup
with app.app_context():
    database.init_db()

def get_current_user():
    if "user_id" in session:
        return {
            "id": session["user_id"],
            "username": session.get("username", "Student"),
            "full_name": session.get("full_name", "Student"),
            "email": session.get("email", ""),
            "department": session.get("department", "General")
        }
    return None

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("chat_page"))
    return redirect(url_for("login_page"))

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if "user_id" in session:
        return redirect(url_for("chat_page"))
        
    error = None
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        
        if not identifier or not password:
            error = "Please enter both username/email and password."
        else:
            success, result = database.authenticate_user(identifier, password)
            if success:
                session["user_id"] = result["id"]
                session["username"] = result["username"]
                session["full_name"] = result["full_name"]
                session["email"] = result["email"]
                session["department"] = result.get("department", "General")
                return redirect(url_for("chat_page"))
            else:
                error = result
                
    chatbot = get_chatbot()
    college_info = chatbot.get_college_info()
    return render_template("login.html", error=error, college_info=college_info)

@app.route("/signup", methods=["GET", "POST"])
def signup_page():
    if "user_id" in session:
        return redirect(url_for("chat_page"))
        
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        full_name = request.form.get("full_name", "").strip()
        department = request.form.get("department", "Computer Science & Engineering").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        if not username or not email or not full_name or not password:
            error = "All fields are required."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must be at least 6 characters long."
        elif len(username) < 3:
            error = "Username must be at least 3 characters long."
        else:
            success, result = database.register_user(username, email, password, full_name, department)
            if success:
                # Automatically log in new student
                session["user_id"] = result["id"]
                session["username"] = result["username"]
                session["full_name"] = result["full_name"]
                session["email"] = result["email"]
                session["department"] = department
                return redirect(url_for("chat_page"))
            else:
                error = result
                
    chatbot = get_chatbot()
    college_info = chatbot.get_college_info()
    return render_template("signup.html", error=error, college_info=college_info)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

@app.route("/chat")
def chat_page():
    user = get_current_user()
    if not user:
        return redirect(url_for("login_page"))
        
    chatbot = get_chatbot()
    college_info = chatbot.get_college_info()
    categories = sorted(list(chatbot.categories))
    suggestions = chatbot.get_quick_suggestions()
    initial_history = database.get_chat_history(user["id"], limit=50)
    
    return render_template(
        "index.html",
        user=user,
        college_info=college_info,
        categories=categories,
        suggestions=suggestions,
        initial_history=initial_history
    )

@app.route("/api/chat", methods=["POST"])
def api_chat():
    user = get_current_user()
    if not user:
        return jsonify({"status": "error", "message": "Authentication required"}), 401
        
    data = request.get_json(silent=True) or {}
    user_message = data.get("message", "").strip()
    
    if not user_message:
        return jsonify({"status": "error", "message": "Message cannot be empty"}), 400
        
    # 1. Save user's question to chat history
    _, user_timestamp = database.save_chat_message(user["id"], "user", user_message)
    
    # 2. Process query with NLP chatbot
    chatbot = get_chatbot()
    response_data = chatbot.get_response(user_message)
    bot_reply = response_data.get("answer", "")
    
    # 3. Save chatbot's answer to chat history
    _, bot_timestamp = database.save_chat_message(user["id"], "bot", bot_reply)
    
    return jsonify({
        "status": "success",
        "reply": bot_reply,
        "category": response_data.get("category"),
        "confidence": response_data.get("confidence", 0.0),
        "is_fallback": response_data.get("is_fallback", False),
        "timestamp": bot_timestamp
    })

@app.route("/api/history", methods=["GET"])
def api_history():
    user = get_current_user()
    if not user:
        return jsonify({"status": "error", "message": "Authentication required"}), 401
        
    history = database.get_chat_history(user["id"], limit=100)
    return jsonify({"status": "success", "history": history})

@app.route("/api/history/clear", methods=["POST"])
def api_clear_history():
    user = get_current_user()
    if not user:
        return jsonify({"status": "error", "message": "Authentication required"}), 401
        
    database.clear_chat_history(user["id"])
    return jsonify({"status": "success", "message": "Chat history cleared successfully."})

@app.route("/api/suggestions", methods=["GET"])
def api_suggestions():
    chatbot = get_chatbot()
    return jsonify({
        "status": "success",
        "suggestions": chatbot.get_quick_suggestions(),
        "college_info": chatbot.get_college_info()
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
