import json
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from models.bug import Bug
from services.ai_service import AIService

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    def calculate_cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """
        Calculates cosine similarity between two vectors.
        OpenAI embeddings are unit-normalized, so cosine similarity is just the dot product.
        """
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        return dot_product

    def search_similar_bugs(
        self, 
        db: Session, 
        error_message: str, 
        project_name: str = None, 
        limit: int = 5,
        min_similarity: float = 0.0
    ) -> List[Tuple[Bug, float]]:
        """
        Searches the SQLite database for bugs similar to the input error message.
        Returns a list of tuples containing (Bug, similarity_score) sorted by similarity descending.
        """
        if not error_message.strip():
            return []

        # Generate embedding for the input error message
        query_embedding = self.ai_service.generate_embedding(error_message)
        
        # Query bugs from DB
        query = db.query(Bug)
        if project_name:
            query = query.filter(Bug.project_name == project_name)
        
        bugs = query.all()
        results = []

        for bug in bugs:
            bug_embedding = None
            if bug.embedding:
                try:
                    bug_embedding = json.loads(bug.embedding)
                except Exception as e:
                    logger.error(f"Failed to parse embedding for bug {bug.id}: {e}")
            
            # If embedding is missing in DB, generate and save it (self-healing cache)
            if not bug_embedding:
                logger.info(f"Generating missing embedding for bug {bug.id}")
                # We use the error message to generate the embedding
                bug_embedding = self.ai_service.generate_embedding(bug.error_message)
                bug.embedding = json.dumps(bug_embedding)
                db.add(bug)
                db.commit()
            
            similarity = self.calculate_cosine_similarity(query_embedding, bug_embedding)
            if similarity >= min_similarity:
                results.append((bug, similarity))

        # Sort by similarity descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
