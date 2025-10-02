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
sigma_rssi = 3.0


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
    return d0 * 10 ** ((rssi_d0 - rssi) / (10 * n))


def var_distance_from_rssi(d: float) -> float:
    fac = (d * math.log(10) / (10.0 * n))
    return (fac ** 2) * (sigma_rssi ** 2)


# === EKF ===
class EKF:
    def __init__(self, dt=0.1):
        self.dt = dt
        self.x = [0, 0, 0, 0]  # [x, y, vx, vy]

    def predict(self):
        dt = self.dt
        self.x[0] += self.x[2] * dt
        self.x[1] += self.x[3] * dt

    def update(self, z: Position):
        k = 0.5
        self.x[0] += k * (z.x - self.x[0])
        self.x[1] += k * (z.y - self.x[1])

    def get_state(self) -> Position:
        return Position(self.x[0], self.x[1])


ekf = EKF(dt=0.1)


def get_board_pos(data: list[StationRssi]) -> Position:
    if len(data) < 3:
        return None

    stations_pos = load_stations()
    ekf.predict()

    data_sorted = sorted(data, key=lambda s: s.rssi, reverse=True)
    s1, s2, s3 = data_sorted[:3]
    c1, c2, c3 = stations_pos[s1.name], stations_pos[s2.name], stations_pos[s3.name]

    r1 = rssi_to_distance(s1.rssi)
    d2 = rssi_to_distance(s2.rssi)
    d3 = rssi_to_distance(s3.rssi)

    def unit_vector(a: Position, b: Position):
        dx, dy = b.x - a.x, b.y - a.y
        l = math.hypot(dx, dy)
        return (dx/l, dy/l) if l != 0 else (1, 0)

    def point_on_circle(center: Position, radius: float, toward: Position, invert=False) -> Position:
        ux, uy = unit_vector(center, toward)
        if invert:
            ux, uy = -ux, -uy
        return Position(center.x + ux*radius, center.y + uy*radius)

    def pull_error(p: Position, beacon: Position, dist: float) -> float:
        actual = math.hypot(p.x - beacon.x, p.y - beacon.y)
        return abs(actual - dist)

    candidates = []
    for inv2 in (False, True):
        for inv3 in (False, True):
            p2 = point_on_circle(c1, r1, c2, invert=inv2)
            p3 = point_on_circle(c1, r1, c3, invert=inv3)

            e2 = pull_error(p2, c2, d2)
            e3 = pull_error(p3, c3, d3)

            w2 = 1 / (e2 + 1e-3)
            w3 = 1 / (e3 + 1e-3)
            vx = (p2.x * w2 + p3.x * w3) / (w2 + w3)
            vy = (p2.y * w2 + p3.y * w3) / (w2 + w3)

            dx, dy = vx - c1.x, vy - c1.y
            l = math.hypot(dx, dy)
            if l == 0:
                pos = p2
            else:
                pos = Position(c1.x + dx/l*r1, c1.y + dy/l*r1)

            total_error = pull_error(pos, c2, d2) + pull_error(pos, c3, d3)
            candidates.append((total_error, pos))

    best_err, best_pos = min(candidates, key=lambda x: x[0])
    ekf.update(best_pos)
    return ekf.get_state()
