from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from quiz_data import quiz_bank #load quiz data
from datetime import datetime
from pathlib import Path #to find user_logs.json
from typing import List, Optional
import json
import random

app = FastAPI() # uvicorn main:app --reload to run the server

# load logs
LOG_FILE = Path("user_logs.json")
if LOG_FILE.exists():
    with open(LOG_FILE, "r") as f:
        student_logs = json.load(f)
else:
    student_logs = {}

# pydantic model
class QuizSubmission(BaseModel):
    student_id: str
    topic: str
    question_id: str
    answer: str
    time_spent: Optional[float] = None
    difficulty: Optional[str] = None

# Topic mapping - frontend sends kebab-case, backend uses Title Case
TOPIC_MAPPING = {
    "fractions": "Fractions",
    "decimals": "Decimals", 
    "angles": "Angles",
    "multi-digit-multiplication": "Multi-digit Multiplication",
    "ratios-and-proportional-relationships": "Ratios and Proportional Relationships",
    "statistics": "Statistics"
}

@app.get("/get-question/{student_id}/{topic}")
def get_question(student_id: str, topic: str):
    # Map frontend topic to backend topic
    mapped_topic = TOPIC_MAPPING.get(topic.lower(), topic.title())
    
    print(f"Frontend topic: {topic}")
    print(f"Mapped topic: {mapped_topic}")
    print(f"Available topics in quiz_bank: {list(quiz_bank.keys())}")
    
    topic_questions = quiz_bank.get(mapped_topic, {})
    
    if not topic_questions:
        return {"question": f"No questions found for topic: {mapped_topic}"}

    for question_text, qdata in topic_questions.items():
        print(f"Checking question: {question_text} (difficulty: {qdata.get('difficulty')})")
        if qdata.get("difficulty") == "easy":
            return {
                "id": question_text,
                "question": question_text,
                "difficulty": qdata["difficulty"]
            }

    return {"question": "No easy question found in this topic."}

# api route
@app.post("/check-answer")
def check_answer(submission: QuizSubmission = Body(...)):
    student_id = submission.student_id
    topic = submission.topic
    question = submission.question_id.strip()
    answer = submission.answer.strip()
    time_spent = submission.time_spent or 30
    difficulty = submission.difficulty or "easy"
    
    print(f"DEBUG: Checking topic '{topic}', question '{question}'")

    # check if the question exists
    if topic not in quiz_bank or question not in quiz_bank[topic]:
        print(f"ERROR: Question not found. Topic: {topic}, Question: {question}")
        print(f"Available topics: {list(quiz_bank.keys())}")
        if topic in quiz_bank:
            print(f"Available questions in {topic}: {list(quiz_bank[topic].keys())[:3]}...")
        return {"message": "❌ Question does not exist.", "points": 0}

    question_data = quiz_bank[topic][question]
    correct_answer = question_data["correct_answer"]
    wrong_answers = question_data.get("wrong_answers", {})
    explanation = question_data.get("default_explanation", "Try again.")
    
    #check if correct
    try:
        # Try numerical comparison
        is_correct = float(answer.strip()) == float(correct_answer)
    except:
        # Fallback to string comparison
        is_correct = answer.strip().lower() == str(correct_answer).strip().lower()

    # calculate points
    points = 0
    if is_correct:
        # base points
        points = 100

        # Difficulty multiplier
        difficulty_multipliers = {
            'easy': 1,
            'medium': 1.5,
            'hard': 2
        }
        points *= difficulty_multipliers.get(difficulty.lower(), 1)

        # speed bonus
        speed_bonus = 0
        if time_spent <5:
            speed_bonus = 50
        elif time_spent < 10:
            speed_bonus = 25
        elif time_spent < 15:
            speed_bonus = 10
        
        points = round(points + speed_bonus)

    # log
    log_entry = {
        "question": question,
        "answer": answer,
        "correct": is_correct,
        "points": points,
        "time_spent": time_spent,
        "difficulty": difficulty,
        "timestamp": datetime.now().isoformat()
    }

    student_logs.setdefault(student_id, []).append(log_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(student_logs, f, indent=2)

    #feedback
    if is_correct:
        return {
            "is_correct": True,
            "message": "Correct!",
            "points": points
        }
    elif answer in wrong_answers:
        return {
            "is_correct": False,
            "message": wrong_answers[answer],
            "points": 0,
            "default_explanation": explanation
        } 
    else:
        return {
            "is_correct": False,
            "message": explanation,
            "points": 0
        }

@app.get("/next-difficulty/{student_id}")
def get_next_difficulty(student_id: str):
    logs = student_logs.get(student_id, [])

    if len(logs) == 0:
        return {"difficulty": "easy"} #default if no data
    
    # check last 2 answers
    recent_logs = logs[-2:]
    correct_count = sum(1 for log in recent_logs if log["correct"])

    if correct_count == 2:
        return {"difficulty": "hard"}
    elif correct_count == 1:
        return {"difficulty": "medium"}  
    else:
        return {"difficulty": "easy"}

@app.post("/next-question/{student_id}/{topic}")
async def get_next_question(student_id: str, topic: str, served_questions: List[str] = Body(...)):
    # Map frontend topic to backend topic
    mapped_topic = TOPIC_MAPPING.get(topic.lower(), topic)
    
    print(f"DEBUG: Frontend topic: '{topic}'")
    print(f"DEBUG: Mapped topic: '{mapped_topic}'")
    print(f"DEBUG: Available topics in quiz_bank: {list(quiz_bank.keys())}")
    
    # Get difficulty based on student's progress
    difficulty_response = get_next_difficulty(student_id)
    difficulty = difficulty_response["difficulty"]
    
    print(f"DEBUG: Student {student_id}, Topic: {mapped_topic}, Difficulty: {difficulty}")
    print(f"DEBUG: Served questions so far: {served_questions}")
    
    # Check if topic exists FIRST
    if mapped_topic not in quiz_bank:
        print(f"ERROR: Topic '{mapped_topic}' not found in quiz_bank")
        raise HTTPException(status_code=404, detail=f"Topic '{mapped_topic}' not found. Available topics: {list(quiz_bank.keys())}")
    
    # Get all questions for this topic
    questions = quiz_bank[mapped_topic]
    print(f"DEBUG: Total questions in {mapped_topic}: {len(questions)}")
    
    # Filter by difficulty and exclude already served questions
    available_questions = [
        q for q in questions 
        if q not in served_questions and questions[q]["difficulty"] == difficulty
    ]
    
    print(f"DEBUG: Available {difficulty} questions: {len(available_questions)}")
    if available_questions:
        print(f"DEBUG: Available questions: {available_questions[:3]}...")  # Show first 3
    
    # If no questions of current difficulty, try easy as fallback
    if not available_questions:
        if difficulty != "easy":
            available_questions = [
                q for q in questions 
                if q not in served_questions and questions[q]["difficulty"] == "easy"
            ]
            print(f"DEBUG: Fallback to easy questions: {len(available_questions)} found")
        
        if not available_questions:
            print("DEBUG: No questions available at all")
            return {"question": "No more questions available.", "difficulty": "N/A"}
    
    # Select a random question from available ones
    selected_question_key = random.choice(available_questions)
    data = questions[selected_question_key]
    
    print(f"DEBUG: Selected question: '{selected_question_key}' (difficulty: {data['difficulty']})")

    # Create choices (wrong answers + correct answer, shuffled)
    choices = list(data["wrong_answers"].keys()) + [data["correct_answer"]]
    random.shuffle(choices)

    return {
        "id": selected_question_key,
        "question": selected_question_key,
        "choices": choices,
        "difficulty": data["difficulty"],
        "topic": mapped_topic  # Return the mapped topic
    }
    
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # or ["http://127.0.0.1:5500"] for stricter security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)