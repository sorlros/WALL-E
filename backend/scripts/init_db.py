from db.database import engine, Base
from db.models import Profile, Mission, Detection

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")
