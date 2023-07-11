import os
import tempfile

from pdf_api.models import Base
from pdf_api.db import engine

TMP_DIR = tempfile.gettempdir()
os.environ["DB_DSN"] = f"sqlite:///{TMP_DIR}/db.sqlite?"
os.environ["JWT_SECRET"] = "secret"

Base.metadata.create_all(engine)
