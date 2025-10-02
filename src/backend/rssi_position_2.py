from dataclasses import dataclass
import os
import csv
import math

CUR_DIR = os.path.dirname(os.path.realpath(__file__))
STATIONS_PATH = os.path.join(CUR_DIR, "data", "beacons.txt")

@dataclass
class Position:
    x: float
    y: float

@dataclass
class StationRssi:
    name: str
    rssi: int

# === Конфигурация ===
d0 = 1.0
rssi_d0 = -40
n = 2.75
sigma_rssi = 3.0  # стандартное отклонение RSSI (дБ)

def check_stations_path() -> bool:
    return os.path.exists(STATIONS_PATH)

def load_stations() -> dict[str, Position]:
    stations: dict[str, Position] = {}
    with open(STATIONS_PATH, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter=";")
        for row in reader:
            stations[row["Name"]] = Position(float(row["X"]), float(row["Y"]))
    return stations

def rssi_to_distance(rssi: float) -> float:
    """Переводит RSSI (дБм) в расстояние (м)"""
    return d0 * 10 ** ((rssi_d0 - rssi) / (10 * n))

def var_distance_from_rssi(d: float) -> float:
    """Дисперсия ошибки измерения расстояния из-за флуктуаций RSSI"""
    fac = (d * math.log(10) / (10.0 * n))
    return (fac ** 2) * (sigma_rssi ** 2)

# === Робастная WLS ===
def robust_wls(data: list[StationRssi], stations_pos: dict[str, Position]):
    if len(data) < 3:
        return None, None

    # RSSI → расстояние
    beacons, dists, vars_ = [], [], []
    for s in data:
        if s.name not in stations_pos:
            continue
        d = rssi_to_distance(s.rssi)
        var_d = var_distance_from_rssi(d)
        beacons.append(stations_pos[s.name])
        dists.append(d)
        vars_.append(var_d)

    if len(beacons) < 3:
        return None, None

    # Сортировка по расстояниям: берём 3 ближ + 1 дальний
    idx_sort = sorted(range(len(dists)), key=lambda i: dists[i])
    sel_idx = idx_sort[:3]
    if len(idx_sort) > 3:
        sel_idx.append(idx_sort[-1])

    beacons = [beacons[i] for i in sel_idx]
    dists = [dists[i] for i in sel_idx]
    vars_ = [vars_[i] for i in sel_idx]

    # Начальная оценка — центр масс
    x = sum(b.x for b in beacons) / len(beacons)
    y = sum(b.y for b in beacons) / len(beacons)

    for _ in range(10):
        A, b, w = [], [], []
        for (bx, by), di, var in zip(beacons, dists, vars_):
            r_est = math.hypot(x - bx, y - by)
            if r_est < 1e-6:
                r_est = 1e-6
            A.append(((x - bx) / r_est, (y - by) / r_est))
            b.append(di - r_est)
            w.append(1.0 / var)

        # Huber-робастность
        sigma = (sum((bi**2 for bi in b)) / len(b)) ** 0.5
        c = 1.5 * sigma if sigma > 1e-6 else 1.0
        for i in range(len(b)):
            if abs(b[i]) > c:
                w[i] *= c / abs(b[i])

        # Нормальные уравнения
        AtWA = [[0, 0], [0, 0]]
        AtWb = [0, 0]
        for (ai, aj), bi, wi in zip(A, b, w):
            AtWA[0][0] += wi * ai * ai
            AtWA[0][1] += wi * ai * aj
            AtWA[1][0] += wi * aj * ai
            AtWA[1][1] += wi * aj * aj
            AtWb[0] += wi * ai * bi
            AtWb[1] += wi * aj * bi

        det = AtWA[0][0] * AtWA[1][1] - AtWA[0][1] * AtWA[1][0]
        if abs(det) < 1e-9:
            break

        dx = (AtWb[0] * AtWA[1][1] - AtWb[1] * AtWA[0][1]) / det
        dy = (AtWb[1] * AtWA[0][0] - AtWb[0] * AtWA[1][0]) / det

        x += dx
        y += dy
        if math.hypot(dx, dy) < 1e-3:
            break

    return Position(x, y), AtWA  # AtWA ~ аппрокс ковариации

# === EKF ===
class EKF:
    def __init__(self, dt=0.1):
        self.dt = dt
        self.x = [0, 0, 0, 0]  # [x, y, vx, vy]
        self.P = [[100 if i==j else 0 for j in range(4)] for i in range(4)]

    def predict(self):
        dt = self.dt
        x, y, vx, vy = self.x
        self.x = [x + vx*dt, y + vy*dt, vx, vy]
        # P можно обновить упрощённо (без NumPy)
        # пока оставим как константную аппроксимацию

    def update(self, z: Position):
        k = 0.5  # простое приближение Kalman gain
        self.x[0] += k * (z.x - self.x[0])
        self.x[1] += k * (z.y - self.x[1])

    def get_state(self) -> Position:
        return Position(self.x[0], self.x[1])

ekf = EKF(dt=0.1)

# === Главная функция ===
def locate_from_rssi(data: list[StationRssi]) -> Position | None:
    stations_pos = load_stations()
    ekf.predict()
    pos, cov = robust_wls(data, stations_pos)
    if pos is not None:
        ekf.update(pos)
    return ekf.get_state()
