import os
import csv
import random
import json
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from .forms import RegistrationForm, LoginForm
from .models import User, QuizAttempt
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

def load_questions():
    csv_path = os.path.join(os.path.dirname(__file__), 'static', 'questions.csv')
    questions = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cleaned_row = {k: (str(v).strip() if v is not None else "") for k, v in row.items()}
            questions.append(cleaned_row)
    return questions

@main.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():
    # Initialize stats in session if not already present.
    if "stats" not in session:
        session["stats"] = {"total": 0, "correct": 0, "incorrect": 0}

    # Load questions if not already in session.
    if "quiz_questions" not in session:
        raw_questions = load_questions()
        simple_questions = []
        for q in raw_questions:
            question_text = q.get("question", "")
            options = [
                q.get("option_a", ""),
                q.get("option_b", ""),
                q.get("option_c", ""),
                q.get("option_d", "")
            ]
            correct_answer_raw = q.get("correct_answer", "").strip()
            if correct_answer_raw.upper() in ["A", "B", "C", "D"]:
                mapping_index = {"A": 0, "B": 1, "C": 2, "D": 3}
                index = mapping_index[correct_answer_raw.upper()]
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
    randomized_answers = current_q["options"].copy()
    random.shuffle(randomized_answers)

    if request.method == "POST":
        # Exit button functionality.
        if "exit" in request.form:
            # Persist quiz-attempt to the database
            stats = session.get("stats", {"total": 0, "correct": 0, "incorrect": 0})
            if stats["total"] > 0:
                attempt = QuizAttempt(
                    user_id=current_user.id,
                    correct_count=stats["correct"],
                    total_count=stats["total"]
                )
                db.session.add(attempt)
                db.session.commit()

            # Clear quiz session data
            session.pop("quiz_questions", None)
            session.pop("current_question_idx", None)
            session.pop("last_feedback", None)
            session.pop("stats", None)

            flash("You have exited the quiz and your attempt was saved.", "info")
            return redirect(url_for("main.home"))

        # Process the answer.
        selected_answer = request.form.get("answer")
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
    # 1) Fetch all attempts for this user, ordered by timestamp
    attempts = (
        QuizAttempt.query
                   .filter_by(user_id=current_user.id)
                   .order_by(QuizAttempt.taken_on)
                   .all()
    )

    # 2) Compute aggregate stats
    total_quizzes   = len(attempts)
    total_correct   = sum(a.correct_count for a in attempts)
    total_incorrect = sum((a.total_count - a.correct_count) for a in attempts)
    avg_accuracy    = (
        round(sum(a.accuracy for a in attempts) / total_quizzes, 1)
        if total_quizzes else 0
    )

    # 3) Prepare data for Chart.js
    labels = [a.taken_on.strftime("%Y-%m-%d %H:%M") for a in attempts]
    data   = [a.accuracy for a in attempts]
    chart_data = json.dumps({
        'labels': labels,
        'data':   data
    })

    return render_template(
        "stats.html",
        total_quizzes=total_quizzes,
        total_correct=total_correct,
        total_incorrect=total_incorrect,
        avg_accuracy=avg_accuracy,
        chart_data=chart_data
    )