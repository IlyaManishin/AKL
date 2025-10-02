from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import pathlib

from app_state import GlobalState, AppStates
from backend.data import db
app = FastAPI()

# Абсолютный путь к каталогу "static" (src/backend/fastapi_app/static)
static_path = pathlib.Path(__file__).parent / "static"

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory=static_path), name="static")
global_state = GlobalState()


@app.get("/", response_class=HTMLResponse)
async def root():
    index_file = static_path / "index.html"
    return index_file.read_text(encoding="utf-8")


@app.post("/api/delete_last_way")
async def delete_route():
    db.session.query(db.BoardPosition).delete()
    return {}


@app.post("/api/start_way")
async def start_route():
    global_state.set_state(AppStates.WRITE_WAY)
    db.session.query(db.BoardPosition).delete()
    return {}


@app.post("/api/finish_way")
async def finish_route():
    global_state.set_state(AppStates.WAITING)
    return {}


@app.get("/api/check_board")
async def check_payment():
    return {"res": global_state.is_board_turn_on()}


@app.get("/api/get_positions")
async def get_positions():
    pos_objs = db.session.query(db.BoardPosition).all()
    positions = [i.to_dict() for i in pos_objs]
    res = {
        "positions": positions
    }
    return res
