from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import pathlib

app = FastAPI()

# Абсолютный путь к каталогу "static" (src/backend/fastapi_app/static)
static_path = pathlib.Path(__file__).parent / "static"

# Подключаем статические файлы
app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    index_file = static_path / "index.html"
    return index_file.read_text(encoding="utf-8")


# --- API заглушки ---
@app.post("/api/delete_route")
async def delete_route():
    return {"status": "delete_route placeholder"}


@app.post("/api/start_route")
async def start_route():
    return {"status": "start_route placeholder"}


@app.post("/api/finish_route")
async def finish_route():
    return {"status": "finish_route placeholder"}


@app.get("/api/check_payment")
async def check_payment():
    return {"status": "check_payment placeholder"}
