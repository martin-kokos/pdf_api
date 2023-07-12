import os
import tempfile

TMP_DIR = tempfile.gettempdir()
os.environ["DB_DSN"] = f"sqlite:///{TMP_DIR}/db.sqlite?"
os.environ["JWT_SECRET"] = "secret"


from pdf_api.models import Base
from pdf_api.db import engine

Base.metadata.create_all(engine)
