__author__ = 'dmiller'

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

# sql tests
engine = create_engine('sqlite:///data.db')

Base = declarative_base()

# define tables
class Groups(Base):
    __tablename__ = 'groups'

    id = Column(Integer, primary_key=True)
    name = Column(String(700), unique=True, index=True)

class Articles(Base):
    __tablename__ = 'articles'

    id = Column(Integer, length=5, primary_key=True)
    h_subject = Column(String(1024))
    h_from = Column(String(1024))
    h_date = Column(DateTime)
    h_message_id = Column(String(700), unique=True, index=True)
    h_references = Column(String(1024))
    h_bytes = Column(Integer)
    h_lines = Column(Integer)

# create all tables
Base.metadata.create_all(engine)