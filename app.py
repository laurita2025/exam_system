from flask import Flask, render_template, request, redirect, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import random
import datetime
import copy

from config import *
from questions import questions

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Conexión MongoDB Atlas
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
try:
    client.admin.command("ping")
    print("Conectado a MongoDB Atlas")
except Exception as e:
    raise RuntimeError(f"Error conectando a MongoDB Atlas: {e}")

db = client[DB_NAME]

students = db.students
exams = db.exams
logs = db.logs


@app.route('/')
def home():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    name = request.form['name']
    carnet = request.form['carnet']

    # Verificar si ya rindió
    if students.find_one({"carnet": carnet}):
        return "Ya rendiste este examen."

    # Guardar estudiante
    student_id = students.insert_one({
        "name": name,
        "carnet": carnet,
        "created_at": datetime.datetime.utcnow()
    }).inserted_id

    # Copia segura para no modificar preguntas originales
    selected_questions = copy.deepcopy(random.sample(questions, 20))

    for q in selected_questions:
        random.shuffle(q["options"])

    # Crear examen
    exam_id = exams.insert_one({
        "student_id": student_id,
        "questions": selected_questions,
        "answers": {},
        "warnings": 0,
        "status": "active",
        "score": 0,
        "created_at": datetime.datetime.utcnow()
    }).inserted_id

    session["exam_id"] = str(exam_id)

    return redirect('/exam')


def get_exam():
    exam_id = session.get("exam_id")

    if not exam_id:
        return None

    try:
        return exams.find_one({"_id": ObjectId(exam_id)})
    except:
        return None


@app.route('/exam')
def exam():
    exam = get_exam()

    if not exam:
        return redirect('/')

    if exam.get("status") == "expelled":
        return render_template("expelled.html")

    return render_template(
        "exam.html",
        exam=exam,
        time=EXAM_TIME
    )


@app.route('/submit', methods=['POST'])
def submit():
    exam = get_exam()

    if not exam:
        return redirect('/')

    if exam.get("status") == "expelled":
        if not exam.get("finished_at"):
            exams.update_one(
                {"_id": exam["_id"]},
                {"$set": {"finished_at": datetime.datetime.utcnow()}}
            )
        return render_template("expelled.html")

    answers = request.form.to_dict()
    score = 0
    wrong_details = []

    for i, q in enumerate(exam["questions"]):
        submitted = answers.get(str(i))
        if submitted == q["answer"]:
            score += 1
        else:
            wrong_details.append({
                "number": i + 1,
                "question": q["question"],
                "selected": submitted,
                "correct": q["answer"]
            })

    correct = score
    incorrect = len(wrong_details)
    final_score = (score / len(exam["questions"])) * 100

    if final_score >= 80:
        dashboard_message = "Excelente desempeño 🎉"
    elif final_score >= 60:
        dashboard_message = "Buen trabajo 👍"
    else:
        dashboard_message = "Necesitas mejorar 📚"

    exams.update_one(
        {"_id": exam["_id"]},
        {
            "$set": {
                "answers": answers,
                "score": final_score,
                "status": "finished",
                "finished_at": datetime.datetime.utcnow(),
                "incorrect_count": incorrect,
                "wrong_details": wrong_details,
                "dashboard_message": dashboard_message
            }
        }
    )

    return render_template(
        "result.html",
        score=final_score,
        correct=correct,
        incorrect=incorrect,
        wrong_details=wrong_details
    )


@app.route('/warning', methods=['POST'])
def warning():
    exam = get_exam()

    if not exam:
        return jsonify({"error": "Exam not found"}), 404

    warnings = exam.get("warnings", 0) + 1

    exams.update_one(
        {"_id": exam["_id"]},
        {"$set": {"warnings": warnings}}
    )

    if warnings >= MAX_WARNINGS:
        exams.update_one(
            {"_id": exam["_id"]},
            {
                "$set": {
                    "status": "expelled",
                    "finished_at": datetime.datetime.utcnow(),
                    "score": 0
                }
            }
        )
        return jsonify({"warnings": warnings, "expelled": True, "maxWarnings": MAX_WARNINGS})

    return jsonify({"warnings": warnings, "expelled": False, "maxWarnings": MAX_WARNINGS})


@app.route('/dashboard')
def dashboard():
    all_exams = []
    for exam in exams.find():
        student = students.find_one({"_id": exam["student_id"]})
        incorrect_count = exam.get("incorrect_count", 0)
        wrong_details = exam.get("wrong_details", [])

        if exam.get("status") == "finished" and not wrong_details and exam.get("answers"):
            for i, q in enumerate(exam["questions"]):
                submitted = exam["answers"].get(str(i))
                if submitted != q["answer"]:
                    incorrect_count += 1
                    wrong_details.append({
                        "number": i + 1,
                        "question": q["question"],
                        "selected": submitted,
                        "correct": q["answer"]
                    })

        dashboard_message = exam.get("dashboard_message")
        if not dashboard_message:
            if exam.get("status") == "finished":
                score_value = exam.get("score", 0)
                if score_value >= 80:
                    dashboard_message = "Excelente desempeño 🎉"
                elif score_value >= 60:
                    dashboard_message = "Buen trabajo 👍"
                else:
                    dashboard_message = "Necesitas mejorar 📚"
            elif exam.get("status") == "active":
                dashboard_message = "En curso"
            else:
                dashboard_message = "Expulsado"

        exam["student"] = student
        exam["incorrect_count"] = incorrect_count
        exam["wrong_details"] = wrong_details
        exam["dashboard_message"] = dashboard_message
        all_exams.append(exam)

    return render_template(
        "dashboard.html",
        exams=all_exams
    )


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )