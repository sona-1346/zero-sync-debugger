import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

try:
    import parcel
    HAS_PARCEL = True
    print("✅ Parcel library imported successfully.")
except ImportError:
    HAS_PARCEL = False
    print("❌ Parcel library not found.")

class ParcelMemoryService:
    def __init__(self):
        self.api_key = os.getenv("PARCEL_API_KEY")
        self.client = None

        print("Initializing Parcel Memory Service...")

        if HAS_PARCEL and self.api_key:
            print("API Key found.")
            self.client = True
            print("Parcel service activated.")
        else:
            print("Parcel inactive.")

    def is_active(self):
        return self.client is not None

    def ingest_bug(
        self,
        project_name,
        error_message,
        root_cause,
        solution
    ):
        print("INGEST FUNCTION CALLED")
        print("Project:", project_name)
        print("Error:", error_message)

        if not self.is_active():
            print("Parcel inactive.")
            return False

        print("Parcel memory simulated successfully.")
        return True

    def query_memory(self, project_name, question):
        print("QUERY FUNCTION CALLED")
        print("Question:", question)

        if not self.is_active():
            return None

        return None