from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import asyncio
from typing import Optional, Dict, Any
import os
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="IAVA API Gateway", version="1.0.0")

# Configuration
DJANGO_BASE_URL = os.getenv("DJANGO_BASE_URL", "http://127.0.0.1:8000")
FASTAPI_QUIZ_URL = os.getenv("FASTAPI_QUIZ_URL", "http://127.0.0.1:8001")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class QuizSubmission(BaseModel):
    student_id: str
    topic: str
    question_id: str
    answer: str
    time_spent: Optional[float] = None
    difficulty: Optional[str] = None

class AuthRequest(BaseModel):
    username: str
    password: str

class StudentRegistration(BaseModel):
    name: str
    password: str
    level: str

# Health check endpoints
@app.get("/health")
async def health_check():
    """Gateway health check"""
    return {"status": "healthy", "service": "api-gateway"}

@app.get("/health/services")
async def services_health_check():
    """Check health of downstream services"""
    services_status = {}
    
    async with httpx.AsyncClient() as client:
        # Check Django service
        try:
            django_response = await client.get(f"{DJANGO_BASE_URL}/", timeout=5.0)
            services_status["django"] = {
                "status": "healthy" if django_response.status_code == 200 else "unhealthy",
                "status_code": django_response.status_code
            }
        except Exception as e:
            services_status["django"] = {"status": "unhealthy", "error": str(e)}
        
        # Check FastAPI Quiz service
        try:
            # Assuming you add a health endpoint to your quiz service
            quiz_response = await client.get(f"{FASTAPI_QUIZ_URL}/health", timeout=5.0)
            services_status["quiz_service"] = {
                "status": "healthy" if quiz_response.status_code == 200 else "unhealthy",
                "status_code": quiz_response.status_code
            }
        except Exception as e:
            services_status["quiz_service"] = {"status": "unhealthy", "error": str(e)}
    
    return {"services": services_status}

# Authentication endpoints (proxy to Django)
@app.post("/api/auth/login")
async def login(auth_data: AuthRequest):
    """Proxy login request to Django"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{DJANGO_BASE_URL}/login/",
                data={"username": auth_data.username, "password": auth_data.password},
                timeout=10.0
            )
            
            if response.status_code == 302:  # Redirect indicates success in Django
                return {"status": "success", "message": "Login successful"}
            else:
                return {"status": "error", "message": "Invalid credentials"}
                
        except Exception as e:
            logger.error(f"Login proxy error: {e}")
            raise HTTPException(status_code=500, detail="Authentication service unavailable")

@app.post("/api/auth/register")
async def register(request: Request):
    """Proxy registration request to Django"""
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{DJANGO_BASE_URL}/register/",
                content=body,
                headers={"content-type": request.headers.get("content-type")},
                timeout=10.0
            )
            
            if response.status_code in [200, 302]:
                return {"status": "success", "message": "Registration successful"}
            else:
                return {"status": "error", "message": "Registration failed"}
                
        except Exception as e:
            logger.error(f"Registration proxy error: {e}")
            raise HTTPException(status_code=500, detail="Registration service unavailable")

@app.post("/api/auth/logout")
async def logout():
    """Proxy logout request to Django"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{DJANGO_BASE_URL}/logout/", timeout=5.0)
            return {"status": "success", "message": "Logged out successfully"}
        except Exception as e:
            logger.error(f"Logout proxy error: {e}")
            return {"status": "success", "message": "Logged out successfully"}  # Fail gracefully

# Student management endpoints (proxy to Django)
@app.get("/api/students/{user_id}")
async def get_students(user_id: str):
    """Get students for a parent user"""
    async with httpx.AsyncClient() as client:
        try:
            # This would require adding an API endpoint to your Django app
            response = await client.get(f"{DJANGO_BASE_URL}/api/students/{user_id}/", timeout=10.0)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch students")
                
        except httpx.RequestError as e:
            logger.error(f"Students fetch error: {e}")
            raise HTTPException(status_code=500, detail="Student service unavailable")

@app.post("/api/students/register")
async def register_student(student_data: StudentRegistration, user_id: str):
    """Register a new student"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{DJANGO_BASE_URL}/api/students/register/",
                json={"user_id": user_id, **student_data.dict()},
                timeout=10.0
            )
            
            if response.status_code in [200, 201]:
                return {"status": "success", "message": "Student registered successfully"}
            else:
                return {"status": "error", "message": "Student registration failed"}
                
        except Exception as e:
            logger.error(f"Student registration error: {e}")
            raise HTTPException(status_code=500, detail="Student registration service unavailable")

@app.delete("/api/students/{student_id}")
async def delete_student(student_id: str, user_id: str):
    """Delete a student"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{DJANGO_BASE_URL}/api/students/{student_id}/",
                params={"user_id": user_id},
                timeout=10.0
            )
            
            if response.status_code in [200, 204]:
                return {"status": "success", "message": "Student deleted successfully"}
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to delete student")
                
        except Exception as e:
            logger.error(f"Student deletion error: {e}")
            raise HTTPException(status_code=500, detail="Student deletion service unavailable")

# Quiz endpoints (proxy to FastAPI Quiz service)
@app.get("/api/quiz/question/{student_id}/{topic}")
async def get_quiz_question(student_id: str, topic: str):
    """Get a quiz question for a student"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{FASTAPI_QUIZ_URL}/get-question/{student_id}/{topic}",
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch question")
                
        except httpx.RequestError as e:
            logger.error(f"Quiz question fetch error: {e}")
            raise HTTPException(status_code=500, detail="Quiz service unavailable")

@app.post("/api/quiz/check-answer")
async def check_quiz_answer(submission: QuizSubmission):
    """Check a quiz answer"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{FASTAPI_QUIZ_URL}/check-answer",
                json=submission.dict(),
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to check answer")
                
        except httpx.RequestError as e:
            logger.error(f"Answer check error: {e}")
            raise HTTPException(status_code=500, detail="Quiz service unavailable")

@app.get("/api/quiz/next-difficulty/{student_id}")
async def get_next_difficulty(student_id: str):
    """Get next difficulty level for a student"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{FASTAPI_QUIZ_URL}/next-difficulty/{student_id}",
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to get difficulty")
                
        except httpx.RequestError as e:
            logger.error(f"Difficulty fetch error: {e}")
            raise HTTPException(status_code=500, detail="Quiz service unavailable")

@app.post("/api/quiz/next-question/{student_id}/{topic}")
async def get_next_question(student_id: str, topic: str, request: Request):
    """Get next quiz question"""
    body = await request.body()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{FASTAPI_QUIZ_URL}/next-question/{student_id}/{topic}",
                content=body,
                headers={"content-type": "application/json"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to get next question")
                
        except httpx.RequestError as e:
            logger.error(f"Next question fetch error: {e}")
            raise HTTPException(status_code=500, detail="Quiz service unavailable")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500
        }
    )

# API documentation
@app.get("/")
async def root():
    return {
        "service": "IAVA API Gateway",
        "version": "1.0.0",
        "description": "Gateway service for Django auth and FastAPI quiz services",
        "endpoints": {
            "health": "/health",
            "services_health": "/health/services",
            "docs": "/docs",
            "auth": "/api/auth/*",
            "students": "/api/students/*",
            "quiz": "/api/quiz/*"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)