import os
import csv
import random
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from .forms import RegistrationForm, LoginForm
from .models import User
from .extensions import db, bcrypt

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    return render_template("home.html")

@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        # Hash the password and create the new user
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}! You can now log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # Check if user exists and if the password is correct
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            # Redirect to next page if specified in the query string
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', form=form)

@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

# ------------------------------------------------------------------
# QUIZ ROUTE AND HELPER FUNCTIONALITY BELOW

# Helper function to load questions from CSV
def load_questions():
    csv_path = os.path.join(os.path.dirname(__file__), 'static', 'questions.csv')
    questions = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Clean each value: if it's None, replace it with an empty string,
            # and otherwise force it to be a string.
            cleaned_row = {k: (str(v).strip() if v is not None else "") for k, v in row.items()}
            questions.append(cleaned_row)
    return questions

# Revised Quiz Route with Endless Quiz, an Exit Button, and Stats Tracking
@main.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():
    # Initialize stats in session if not already present.
    # Stats dictionary tracks total answers, correct answers, and incorrect answers.
    if "stats" not in session:
        session["stats"] = {"total": 0, "correct": 0, "incorrect": 0}

    # Load questions if not already in session.
    if "quiz_questions" not in session:
        raw_questions = load_questions()
        simple_questions = []
        for q in raw_questions:
            question_text = q.get("question", "")
            # Build options list from CSV columns: option_a, option_b, option_c, option_d
            options = [
                q.get("option_a", ""),
                q.get("option_b", ""),
                q.get("option_c", ""),
                q.get("option_d", "")
            ]
            # Determine the correct answer text.
            correct_answer_raw = q.get("correct_answer", "").strip()
            if correct_answer_raw.upper() in ["A", "B", "C", "D"]:
                mapping_index = {"A": 0, "B": 1, "C": 2, "D": 3}
                index = mapping_index.get(correct_answer_raw.upper(), 0)
                correct_answer = options[index]
            else:
                correct_answer = correct_answer_raw

            explanation = q.get("explanation", "")
            simple_q = {
                "question": str(question_text),
                "options": [str(opt).strip() for opt in options if opt and str(opt).strip() != ""],
                "correct_answer": str(correct_answer).strip(),
                "explanation": str(explanation).strip()
            }
            simple_questions.append(simple_q)
        
        random.shuffle(simple_questions)
        session["quiz_questions"] = simple_questions
        session["current_question_idx"] = 0

    idx = session.get("current_question_idx", 0)
    questions = session.get("quiz_questions")

    # Endless Quiz Logic: reshuffle if end is reached.
    if idx >= len(questions):
        flash("You've answered all questions! Restarting the quiz.", "info")
        random.shuffle(questions)
        session["quiz_questions"] = questions
        session["current_question_idx"] = 0
        idx = 0

    current_q = questions[idx]

    # Randomize the options order.
    randomized_answers = current_q["options"].copy()
    random.shuffle(randomized_answers)

    if request.method == "POST":
        # Exit button functionality.
        if "exit" in request.form:
            session.pop("quiz_questions", None)
            session.pop("current_question_idx", None)
            session.pop("last_feedback", None)
            flash("You have exited the quiz.")
            return redirect(url_for("main.home"))

        # Process the answer.
        selected_answer = request.form.get("answer")
        # Update stats.
        stats = session.get("stats", {"total": 0, "correct": 0, "incorrect": 0})
        stats["total"] += 1
        if selected_answer == current_q["correct_answer"]:
            stats["correct"] += 1
            feedback = "✅ Correct!"
        else:
            stats["incorrect"] += 1
            feedback = f"❌ Incorrect: {current_q['explanation']}"
        session["stats"] = stats

        session["last_feedback"] = feedback
        session["current_question_idx"] = idx + 1
        return redirect(url_for("main.quiz"))

    feedback = session.pop("last_feedback", None)
    return render_template("quiz.html",
                           question=current_q["question"],
                           answers=randomized_answers,
                           feedback=feedback)

# ------------------------------------------------------------------
# STATS ROUTE
# ------------------------------------------------------------------
@main.route("/stats")
@login_required
def stats():
    # Retrieve the stats from the session. If none exist, set defaults.
    stats = session.get("stats", {"total": 0, "correct": 0, "incorrect": 0})
    return render_template("stats.html", stats=stats)