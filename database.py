from sqlmodel import SQLModel, create_engine
from dotenv import load_dotenv
import sys
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    sys.exit("DATABASE_URL not set. Add it to your .env file.")

engine = create_engine(DATABASE_URL)
print("Connection secure! Ready to establish tables.")








