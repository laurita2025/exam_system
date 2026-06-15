
from flask import Flask, render_template, request, redirect, session, jsonify
from flask_socketio import SocketIO
from pymongo import MongoClient
from bson.objectid import ObjectId
import random, datetime
from config import *
from questions import questions

app = Flask(__name__)
app.secret_key = SECRET_KEY
socketio = SocketIO(app)

client = MongoClient(MONGO_URI)
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

    if students.find_one({"carnet": carnet}):
        return "Ya rendiste este examen."

    student_id = students.insert_one({
        "name": name,
        "carnet": carnet,
        "created_at": datetime.datetime.now()
    }).inserted_id

    selected_questions = random.sample(questions, 20)
    for q in selected_questions:
        random.shuffle(q["options"])

    exam_id = exams.insert_one({
        "student_id": student_id,
        "questions": selected_questions,
        "answers": {},
        "warnings": 0,
        "status": "active",
        "score": 0
    }).inserted_id

    session['exam_id'] = str(exam_id)
    return redirect('/exam')

@app.route('/exam')
def exam():
    exam = exams.find_one({"_id": ObjectId(session['exam_id'])})
    return render_template('exam.html', exam=exam, time=EXAM_TIME)

@app.route('/submit', methods=['POST'])

@app.route('/submit', methods=['POST'])
def submit():
    exam = exams.find_one({"_id": ObjectId(session['exam_id'])})
    answers = request.form
    score = 0

    for i, q in enumerate(exam['questions']):
        if answers.get(str(i)) == q['answer']:
            score += 1

    correct = score
    incorrect = 20 - score
    final_score = (score / 20) * 100

    exams.update_one(
        {"_id": exam["_id"]},
        {"$set": {
            "answers": answers.to_dict(),
            "score": final_score,
            "status": "finished"
        }}
    )

    return render_template(
        "result.html",
        score=final_score,
        correct=correct,
        incorrect=incorrect
    )

@app.route('/warning', methods=['POST'])
def warning():
    exam = exams.find_one({"_id": ObjectId(session['exam_id'])})
    warnings = exam['warnings'] + 1

    exams.update_one({"_id": exam["_id"]}, {"$set": {"warnings": warnings}})

    if warnings >= MAX_WARNINGS:
        exams.update_one({"_id": exam["_id"]}, {"$set": {"status": "expelled"}})

    return jsonify({"warnings": warnings})

@app.route('/dashboard')
def dashboard():
    all_exams = list(exams.find())
    return render_template("dashboard.html", exams=all_exams, db=db)

if __name__ == "__main__":
    socketio.run(app, debug=True)
