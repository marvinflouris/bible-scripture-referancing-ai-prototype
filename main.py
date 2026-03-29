from sqlmodel import SQLModel
from database import engine
import models

def init_database():
    SQLModel.metadata.create_all(engine)
    print("✅ Database connection OK; tables initialized ready and going.")

init_database() 