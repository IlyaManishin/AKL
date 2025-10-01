from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class BLData(Base):
    __tablename__ = "BlData"
    name = Column(String)
    rssi = Column(Integer)

engine = create_engine("sqlite:///test.db")
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()


