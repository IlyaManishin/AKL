import os
from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()


class BoardPosition(Base):
    __tablename__ = "BoardPosition"
    # нужен первичный ключ
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime, default=datetime.now())
    name = Column(String)
    rssi = Column(Integer)

    def to_dict(self) -> dict:
        res = {
            "date": datetime.strftime(self.time, r"%Y:%m:%d %H:%M"),
            "name": self.name,
            "rssi": self.rssi
        }
        return res


CUR_DIR = os.path.dirname(os.path.realpath(__file__))
DB_PATH = os.path.join(CUR_DIR, "data.db")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# пример сохранения записи
if __name__ == "__main__":
    from datetime import datetime
    new_pos = BoardPosition(time=datetime.now(), name="beacon_1", rssi=-73)
    session.add(new_pos)
    session.commit()
    print("Сохранено в data.db")
