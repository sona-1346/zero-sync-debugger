from dotenv import load_dotenv
import os

load_dotenv()

print(os.getenv("PARCEL_API_KEY"))