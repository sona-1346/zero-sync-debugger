import os
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
        else:
            logger.warning("OPENAI_API_KEY environment variable not found. Using Mock AI Service fallback.")
            self.client = None

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generates OpenAI embeddings for similarity matching.
        """
        if not text.strip():
            return [0.0] * 1536
            
        if self.client:
            try:
                response = self.client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"Error generating embedding: {e}")
                # Fallback to a mock embedding size of 1536
                return self._mock_embedding(text)
        else:
            return self._mock_embedding(text)

    def _mock_embedding(self, text: str) -> List[float]:
        """Generates a pseudo-random deterministic embedding for testing/mock mode."""
        import random
        # Seed based on the text hash to be deterministic for the same text
        h = hash(text)
        random.seed(h)
        vec = [random.uniform(-1.0, 1.0) for _ in range(1536)]
        # Normalize to unit length (L2 norm = 1)
        norm = sum(x**2 for x in vec) ** 0.5
        if norm == 0:
            return vec
        return [x / norm for x in vec]

    def analyze_error(self, error_message: str, description: str = "", log_content: str = "") -> Dict[str, str]:
        """
        Uses OpenAI to analyze the error message and generate a structured root cause analysis.
        """
        prompt = f"""You are Zero-Sync Debugger, an elite AI debugging assistant.
Analyze the following error and provide a detailed root cause and solutions.

Error Message:
{error_message}

User Description:
{description}

Logs:
{log_content}

Your response must be a JSON object with the following fields:
1. "root_cause": A detailed explanation of why this error is happening and its context.
2. "solution": Clear step-by-step instructions on how to solve the issue.
3. "prevention_tips": Tips on how to avoid this bug in the future.
4. "suggested_commands": Specific terminal commands (e.g. pip/npm commands, system checks) that the user can run to diagnose or fix the issue.
5. "suggested_code_changes": Actual code snippet examples (before vs after or new files) showing how to patch the bug.
6. "suggested_dependency_fixes": Dependency upgrades, packages to install, or version corrections needed.

Respond ONLY with valid JSON.
"""

        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a senior systems and software debugging engineer. You always output valid, parseable JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2
                )
                content = response.choices[0].message.content
                return json.loads(content)
            except Exception as e:
                logger.error(f"Error analyzing error with OpenAI: {e}")
                return self._mock_analysis(error_message, description)
        else:
            return self._mock_analysis(error_message, description)

    def _mock_analysis(self, error_message: str, description: str) -> Dict[str, str]:
        """Generates mock analysis data when OpenAI API is not available."""
        return {
            "root_cause": f"Mock Root Cause Analysis: The error '{error_message[:60]}...' indicates a potential configuration mismatch or standard runtime exception. User description suggests: {description or 'no additional details provided'}.",
            "solution": "1. Verify environment variables and database connections.\n2. Ensure all project dependencies are installed correctly.\n3. Restart the server/application module.",
            "prevention_tips": "- Add comprehensive logging around resource initialization.\n- Use environment validation libraries like Pydantic settings.\n- Write unit tests for boundary conditions.",
            "suggested_commands": "pip install -r requirements.txt\npython -m unittest discover",
            "suggested_code_changes": "```python\n# Recommended change in config.py\n- database_url = os.getenv('DATABASE_URL')\n+ database_url = os.getenv('DATABASE_URL', 'sqlite:///./default.db')\n```",
            "suggested_dependency_fixes": "Upgrade sqlalchemy to >= 2.0.0"
        }

    def chat_about_bugs(self, history: List[Dict[str, str]], question: str, context: str) -> str:
        """
        Chat assistant that answers questions referencing the historical bugs context.
        """
        system_prompt = f"""You are the Zero-Sync Debugger Chat Assistant.
Your goal is to answer developer questions about past errors, root causes, and solutions.
Use the following historical context about previously recorded bugs and fixes:

---
HISTORICAL CONTEXT:
{context}
---

If the context contains relevant information, use it to explain how similar bugs were resolved.
If the question is about whether we have seen a bug before, analyze the context and explain matches.
Keep your answers professional, technical, clear, and action-oriented. Provide code or command examples where necessary.
"""

        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": question})

        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.3
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"Error in chat with OpenAI: {e}")
                return f"Mock Chat Assistant: I received your question: '{question}'. Unfortunately, I was unable to connect to the OpenAI API, but looking at my historical records, this resembles known patterns of project initialization issues. Let me know if you want to inspect a particular bug ID from the history."
        else:
            # RAG Mock Answer
            if context.strip():
                return f"Mock Chat Assistant: Based on the historical bugs in database, we have encountered similar errors. For instance:\n{context[:300]}...\nTypically, this is fixed by verifying setup and dependencies."
            else:
                return f"Mock Chat Assistant: I couldn't find any similar bugs in our history matching your query '{question}'. Could you provide more details or submit the error first?"
