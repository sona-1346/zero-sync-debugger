import os
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Try to import parcle
try:
    from parcle import Parcle
    HAS_PARCLE = True
except ImportError:
    HAS_PARCLE = False
    logger.warning("Parcle Python library is not installed. Will use local memory fallback.")

class ParcleMemoryService:
    def __init__(self):
        self.api_key = os.getenv("PARCLE_API_KEY")
        self.client = None
        
        if HAS_PARCLE and self.api_key:
            try:
                self.client = Parcle(api_key=self.api_key)
                logger.info("Parcle memory client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Parcle client: {e}. Falling back to local memory.")
                self.client = None
        else:
            logger.info("PARCLE_API_KEY not found or library missing. Operating in local memory fallback mode.")

    def is_active(self) -> bool:
        """Returns True if Parcle API is active and connected, False if falling back to local."""
        return self.client is not None

    def ingest_bug(self, project_name: str, error_message: str, root_cause: str, solution: str) -> bool:
        """
        Ingests a bug and its solution as dialogue history into the memory layer.
        """
        if self.is_active():
            try:
                # Store the error as the user statement and root cause/solution as the assistant response.
                # Use project_name as the user_id to isolate memory namespaces.
                user_id = project_name.replace(" ", "_").lower()
                messages = [
                    {"role": "user", "content": f"New error encountered: {error_message}"},
                    {"role": "assistant", "content": f"Analysis:\nRoot Cause: {root_cause}\nSolution: {solution}"}
                ]
                self.client.ingest_dialog(user_id=user_id, messages=messages)
                logger.info(f"Ingested bug memory to Parcle for project: {project_name}")
                return True
            except Exception as e:
                logger.error(f"Error ingesting bug into Parcle: {e}")
                return False
        else:
            # Local fallback - we rely on SQLite database persistence
            logger.info("Local fallback: Ingested to local database only.")
            return True

    def query_memory(self, project_name: str, question: str) -> Optional[str]:
        """
        Queries Parcle Memory for answers based on historical context.
        """
        if self.is_active():
            try:
                user_id = project_name.replace(" ", "_").lower()
                answer = self.client.ask(user_id=user_id, question=question)
                if hasattr(answer, "text"):
                    return answer.text
                return str(answer)
            except Exception as e:
                logger.error(f"Error querying Parcle memory: {e}")
                return None
        return None
