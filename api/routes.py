import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database.db import get_db
from models.bug import (
    Bug, 
    BugSubmitRequest, 
    BugAnalysisResponse, 
    BugResponse, 
    ChatRequest, 
    ChatResponse
)
from services.ai_service import AIService
from services.search_service import SearchService
from memory.parcle_service import ParcleMemoryService

router = APIRouter()

# Instantiate services
ai_service = AIService()
search_service = SearchService(ai_service)
memory_service = ParcleMemoryService()

@router.post("/submit_error", response_model=BugAnalysisResponse)
def submit_error(request: BugSubmitRequest, db: Session = Depends(get_db)):
    """
    Submits a new error. If a similar bug with high confidence (>= 0.85 similarity)
    already exists, returns the cached analysis and solution. Otherwise, generates
    a new analysis via OpenAI, stores it in SQLite, indexes it in Parcle, and returns it.
    """
    error_msg = request.error_message.strip()
    if not error_msg:
        raise HTTPException(status_code=400, detail="Error message cannot be empty.")

    # 1. Search for similar bugs in the database
    similar_bugs = search_service.search_similar_bugs(
        db=db, 
        error_message=error_msg, 
        project_name=request.project_name, 
        limit=1
    )

    SIMILARITY_THRESHOLD = 0.85

    if similar_bugs and similar_bugs[0][1] >= SIMILARITY_THRESHOLD:
        matched_bug, score = similar_bugs[0]
        # Parse the structured text from the solution or use default format
        # If the root cause or solution is already saved, return it
        
        # We try to reconstruct structured fields if they were stored.
        # Since we store root_cause and solution as columns, let's extract them.
        # If we need prevention tips or commands, we can look if we can extract them
        # from solution or generate them, but we will store structured details or format
        # them nicely. To ensure we return a clean BugAnalysisResponse:
        
        # Try to parse solution if it is in JSON or formatted. If it's a standard text column,
        # we can return it. Let's make sure the Bug model columns are filled correctly.
        
        # Let's extract prevention tips, commands, code changes, and dependency fixes.
        # Since SQLite stores `solution` and `root_cause`, we can store them in database.
        # Wait, how does SQLite store the extra fields? 
        # In a real system, we can store them as parts of root_cause or solution.
        # Let's make sure that when we save a bug, we serialize extra metadata or store it in `solution` as JSON,
        # or we just split the columns.
        # Wait! To make the Bug database matches the specification:
        # "bugs: id, error_message, root_cause, solution, timestamp"
        # Since we must follow the exact database tables specification:
        # "bugs: id, error_message, root_cause, solution, timestamp"
        # We can store the solution, prevention tips, commands, code changes, and dependency fixes
        # inside the `solution` column as a JSON string, or format it as Markdown text!
        # But wait! If we store the solution as a JSON string inside the `solution` column,
        # we can easily deserialize it back into its structured fields!
        # Let's check how we do that. Yes! We can store the JSON string of:
        # { "solution": "...", "prevention_tips": "...", "suggested_commands": "...", "suggested_code_changes": "...", "suggested_dependency_fixes": "..." }
        # inside the `solution` column!
        # This is brilliant, because it fully satisfies the database schema requirement (we only need the `solution` column)
        # while keeping the data structured! Let's implement that!
        
        try:
            solution_data = json.loads(matched_bug.solution)
            sol_text = solution_data.get("solution", matched_bug.solution)
            prevention = solution_data.get("prevention_tips", "Ensure correct environment setup.")
            commands = solution_data.get("suggested_commands", "")
            code_changes = solution_data.get("suggested_code_changes", "")
            dep_fixes = solution_data.get("suggested_dependency_fixes", "")
        except Exception:
            # Fallback if solution is plain text
            sol_text = matched_bug.solution
            prevention = "Ensure configurations are correct."
            commands = ""
            code_changes = ""
            dep_fixes = ""

        return BugAnalysisResponse(
            root_cause=matched_bug.root_cause,
            solution=sol_text,
            prevention_tips=prevention,
            suggested_commands=commands,
            suggested_code_changes=code_changes,
            suggested_dependency_fixes=dep_fixes,
            similarity_matched=True,
            similarity_score=score
        )

    # 2. No similarity match. Perform AI analysis.
    analysis = ai_service.analyze_error(
        error_message=error_msg, 
        description=request.description, 
        log_content=request.log_content
    )

    # Save to SQLite DB
    embedding_vector = ai_service.generate_embedding(error_msg)
    
    # Store structured solution fields inside SQLite `solution` column as JSON
    solution_json_data = {
        "solution": analysis.get("solution", ""),
        "prevention_tips": analysis.get("prevention_tips", ""),
        "suggested_commands": analysis.get("suggested_commands", ""),
        "suggested_code_changes": analysis.get("suggested_code_changes", ""),
        "suggested_dependency_fixes": analysis.get("suggested_dependency_fixes", "")
    }
    
    new_bug = Bug(
        project_name=request.project_name or "Default Project",
        error_message=error_msg,
        root_cause=analysis.get("root_cause", ""),
        solution=json.dumps(solution_json_data),
        embedding=json.dumps(embedding_vector)
    )
    
    db.add(new_bug)
    db.commit()
    db.refresh(new_bug)

    # 3. Store in Memory Layer (Parcle API)
    memory_service.ingest_bug(
        project_name=new_bug.project_name,
        error_message=new_bug.error_message,
        root_cause=new_bug.root_cause,
        solution=analysis.get("solution", "")
    )

    return BugAnalysisResponse(
        root_cause=new_bug.root_cause,
        solution=analysis.get("solution", ""),
        prevention_tips=analysis.get("prevention_tips", ""),
        suggested_commands=analysis.get("suggested_commands", ""),
        suggested_code_changes=analysis.get("suggested_code_changes", ""),
        suggested_dependency_fixes=analysis.get("suggested_dependency_fixes", ""),
        similarity_matched=False,
        similarity_score=0.0
    )


@router.post("/analyze_error", response_model=BugAnalysisResponse)
def analyze_error(request: BugSubmitRequest, db: Session = Depends(get_db)):
    """
    Directly analyzes an error without similarity checking and saves the result to SQLite and Parcle.
    """
    error_msg = request.error_message.strip()
    if not error_msg:
        raise HTTPException(status_code=400, detail="Error message cannot be empty.")

    analysis = ai_service.analyze_error(
        error_message=error_msg, 
        description=request.description, 
        log_content=request.log_content
    )

    embedding_vector = ai_service.generate_embedding(error_msg)
    
    solution_json_data = {
        "solution": analysis.get("solution", ""),
        "prevention_tips": analysis.get("prevention_tips", ""),
        "suggested_commands": analysis.get("suggested_commands", ""),
        "suggested_code_changes": analysis.get("suggested_code_changes", ""),
        "suggested_dependency_fixes": analysis.get("suggested_dependency_fixes", "")
    }

    new_bug = Bug(
        project_name=request.project_name or "Default Project",
        error_message=error_msg,
        root_cause=analysis.get("root_cause", ""),
        solution=json.dumps(solution_json_data),
        embedding=json.dumps(embedding_vector)
    )
    
    db.add(new_bug)
    db.commit()
    db.refresh(new_bug)

    memory_service.ingest_bug(
        project_name=new_bug.project_name,
        error_message=new_bug.error_message,
        root_cause=new_bug.root_cause,
        solution=analysis.get("solution", "")
    )

    return BugAnalysisResponse(
        root_cause=new_bug.root_cause,
        solution=analysis.get("solution", ""),
        prevention_tips=analysis.get("prevention_tips", ""),
        suggested_commands=analysis.get("suggested_commands", ""),
        suggested_code_changes=analysis.get("suggested_code_changes", ""),
        suggested_dependency_fixes=analysis.get("suggested_dependency_fixes", ""),
        similarity_matched=False,
        similarity_score=0.0
    )


@router.get("/similar_bugs")
def get_similar_bugs(
    error_message: str = Query(..., description="The error message to search for"),
    project_name: Optional[str] = Query(None, description="Filter by project name"),
    limit: int = Query(5, description="Limit the number of results"),
    db: Session = Depends(get_db)
):
    """
    Find similar bugs based on cosine similarity of embeddings.
    """
    similar = search_service.search_similar_bugs(
        db=db, 
        error_message=error_message, 
        project_name=project_name, 
        limit=limit
    )

    results = []
    for bug, score in similar:
        # Attempt to parse structured solutions
        try:
            solution_data = json.loads(bug.solution)
            sol_text = solution_data.get("solution", bug.solution)
            prevention = solution_data.get("prevention_tips", "")
            commands = solution_data.get("suggested_commands", "")
            code_changes = solution_data.get("suggested_code_changes", "")
            dep_fixes = solution_data.get("suggested_dependency_fixes", "")
        except Exception:
            sol_text = bug.solution
            prevention = ""
            commands = ""
            code_changes = ""
            dep_fixes = ""

        results.append({
            "id": bug.id,
            "project_name": bug.project_name,
            "error_message": bug.error_message,
            "root_cause": bug.root_cause,
            "solution": sol_text,
            "prevention_tips": prevention,
            "suggested_commands": commands,
            "suggested_code_changes": code_changes,
            "suggested_dependency_fixes": dep_fixes,
            "timestamp": bug.timestamp,
            "similarity_score": score
        })
    return results


@router.get("/bug_history")
def get_bug_history(
    project_name: Optional[str] = Query(None, description="Filter by project name"),
    search: Optional[str] = Query(None, description="Keyword search in error, root cause, or solution"),
    db: Session = Depends(get_db)
):
    """
    Retrieves bug history with optional filtering.
    """
    query = db.query(Bug)
    
    if project_name:
        query = query.filter(Bug.project_name == project_name)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Bug.error_message.like(search_filter)) | 
            (Bug.root_cause.like(search_filter)) | 
            (Bug.solution.like(search_filter))
        )
    
    bugs = query.order_by(Bug.timestamp.desc()).all()
    
    results = []
    for bug in bugs:
        try:
            solution_data = json.loads(bug.solution)
            sol_text = solution_data.get("solution", bug.solution)
            prevention = solution_data.get("prevention_tips", "")
            commands = solution_data.get("suggested_commands", "")
            code_changes = solution_data.get("suggested_code_changes", "")
            dep_fixes = solution_data.get("suggested_dependency_fixes", "")
        except Exception:
            sol_text = bug.solution
            prevention = ""
            commands = ""
            code_changes = ""
            dep_fixes = ""

        results.append({
            "id": bug.id,
            "project_name": bug.project_name,
            "error_message": bug.error_message,
            "root_cause": bug.root_cause,
            "solution": sol_text,
            "prevention_tips": prevention,
            "suggested_commands": commands,
            "suggested_code_changes": code_changes,
            "suggested_dependency_fixes": dep_fixes,
            "timestamp": bug.timestamp
        })
    return results


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Chat assistant endpoint. Queries memory/DB and uses AI to answer questions.
    """
    # 1. Search for similar bugs or context related to the user's chat message
    similar_bugs = search_service.search_similar_bugs(
        db=db, 
        error_message=request.message, 
        project_name=request.project_name, 
        limit=3
    )

    # Compile context from matching bugs
    context_parts = []
    for bug, score in similar_bugs:
        try:
            solution_data = json.loads(bug.solution)
            sol_text = solution_data.get("solution", bug.solution)
        except Exception:
            sol_text = bug.solution
            
        context_parts.append(
            f"Bug ID: {bug.id} (Project: {bug.project_name})\n"
            f"Error: {bug.error_message}\n"
            f"Root Cause: {bug.root_cause}\n"
            f"Solution: {sol_text}\n"
            f"Similarity Score: {score:.2f}\n"
        )
    
    context = "\n".join(context_parts) if context_parts else "No similar bugs found in local history."

    # 2. Check Parcle memory layer if active
    if memory_service.is_active():
        parcle_context = memory_service.query_memory(request.project_name, request.message)
        if parcle_context:
            context += f"\nParcle Memory Context:\n{parcle_context}"

    # 3. Generate response using AI
    answer = ai_service.chat_about_bugs(
        history=request.history, 
        question=request.message, 
        context=context
    )

    return ChatResponse(response=answer)
