import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DB_DSN = os.environ["DB_DSN"]
engine = create_engine(DB_DSN, echo=True)

Session = sessionmaker(engine, expire_on_commit=False)
