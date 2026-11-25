from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.database import Base, engine, get_db
from app.models import Snippet
from app.schemas import SnippetCreate, SnippetUpdate, SnippetResponse

from app.executor import (
    run_cpp,
    run_c,
    run_python,
    run_java,
    run_javascript
)


# Create database tables when the application starts
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="MultiCode API",
    description="Backend API for the MultiCode online compiler",
    version="1.0.0",
    lifespan=lifespan
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://multicode-93sh.onrender.com"
        ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# BASIC ROUTES

@app.get("/")
def home():
    return {
        "message": "Welcome to MultiCode API!",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

# CODE EXECUTION

@app.post("/run")
def run_code(data: dict):

    source_code = data.get("code", "")
    language = data.get("language", "")
    custom_input = data.get("input", "")

    if language == "cpp":
        result = run_cpp(source_code, custom_input)

    elif language == "c":
        result = run_c(source_code, custom_input)

    elif language == "python":
        result = run_python(source_code, custom_input)

    elif language == "java":
        result = run_java(source_code, custom_input)

    elif language == "javascript":
        result = run_javascript(source_code, custom_input)

    else:
        return {
            "status": "error",
            "output": f"Language '{language}' is not supported."
        }

    return {
        "language": language,
        **result
    }

# SNIPPET MANAGEMENT

# CREATE SNIPPET
@app.post(
    "/snippets",
    response_model=SnippetResponse,
    status_code=status.HTTP_201_CREATED
)
def create_snippet(
    snippet: SnippetCreate,
    db: Session = Depends(get_db)
):

    new_snippet = Snippet(
        name=snippet.name,
        language=snippet.language,
        code=snippet.code
    )

    db.add(new_snippet)
    db.commit()
    db.refresh(new_snippet)

    return new_snippet


# GET ALL SNIPPETS
@app.get(
    "/snippets",
    response_model=list[SnippetResponse]
)
def get_snippets(
    db: Session = Depends(get_db)
):

    statement = select(Snippet).order_by(
        Snippet.updated_at.desc()
    )

    snippets = db.scalars(statement).all()

    return snippets


# GET ONE SNIPPET
@app.get(
    "/snippets/{snippet_id}",
    response_model=SnippetResponse
)
def get_snippet(
    snippet_id: int,
    db: Session = Depends(get_db)
):

    snippet = db.get(Snippet, snippet_id)

    if snippet is None:
        raise HTTPException(
            status_code=404,
            detail="Snippet not found"
        )

    return snippet


# UPDATE SNIPPET
@app.put(
    "/snippets/{snippet_id}",
    response_model=SnippetResponse
)
def update_snippet(
    snippet_id: int,
    updated_data: SnippetUpdate,
    db: Session = Depends(get_db)
):

    snippet = db.get(Snippet, snippet_id)

    if snippet is None:
        raise HTTPException(
            status_code=404,
            detail="Snippet not found"
        )

    snippet.name = updated_data.name
    snippet.language = updated_data.language
    snippet.code = updated_data.code
    snippet.updated_at = func.now()

    db.commit()
    db.refresh(snippet)

    return snippet


# DELETE SNIPPET
@app.delete(
    "/snippets/{snippet_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_snippet(
    snippet_id: int,
    db: Session = Depends(get_db)
):

    snippet = db.get(Snippet, snippet_id)

    if snippet is None:
        raise HTTPException(
            status_code=404,
            detail="Snippet not found"
        )

    db.delete(snippet)
    db.commit()

    return None