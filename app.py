import asyncio
import os
import time
from datetime import date, datetime

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Direct Flight Finder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

KIWI_BASE = "https://api.tequila.kiwi.com"

AIRPORTS = [
    {"code": "YUL", "name": "Montreal Trudeau", "drive": "0 min"},
    {"code": "YOW", "name": "Ottawa", "drive": "~2 hr"},
    {"code": "YQB", "name": "Quebec City", "drive": "~2.5 hr"},
    {"code": "BTV", "name": "Burlington VT", "drive": "~1.5 hr"},
    {"code": "PBG", "name": "Plattsburgh NY", "drive": "~1 hr"},
    {"code": "SYR", "name": "Syracuse NY", "drive": "~4 hr"},
    {"code": "ALB", "name": "Albany NY", "drive": "~3.5 hr"},
    {"code": "YYZ", "name": "Toronto Pearson", "drive": "~5.5 hr"},
    {"code": "ROC", "name": "Rochester NY", "drive": "~5 hr"},
    {"code": "PWM", "name": "Portland ME", "drive": "~5 hr"},
    {"code": "BGM", "name": "Binghamton NY", "drive": "~5.5 hr"},
    {"code": "YKF", "name": "Waterloo ON", "drive": "~6 hr"},
    {"code": "BUF", "name": "Buffalo NY", "drive": "~6.5 hr"},
]

# Nov 11-15 in DD/MM/YYYY format for Kiwi API
DATE_FROM = "11/11/2026"
DATE_TO = "15/11/2026"
# ISO dates for the frontend
DATES = ["2026-11-11", "2026-11-12", "2026-11-13", "2026-11-14", "2026-11-15"]

AIRPORT_NAMES = {a["code"]: a["name"] for a in AIRPORTS}

# Flight results cache: origin -> (timestamp, results)
_flight_cache: dict[str, tuple[float, list]] = {}
CACHE_TTL = 900  # 15 minutes


def get_api_key() -> str:
    key = os.environ.get("KIWI_API_KEY", "")
    if not key:
        raise HTTPException(
            status_code=500,
            detail="Kiwi API key not configured. Set KIWI_API_KEY in .env (get one at tequila.kiwi.com)",
        )
    return key


def parse_kiwi_flights(origin: str, raw_data: dict) -> list[dict]:
    flights = []
    for flight in raw_data.get("data", []):
        route = flight.get("route", [])
        if len(route) != 1:
            continue  # skip non-direct (shouldn't happen with max_stopovers=0)

        leg = route[0]
        carrier = leg.get("airline", "")
        flight_no = leg.get("flight_no", "")

        local_departure = leg.get("local_departure", "")
        local_arrival = leg.get("local_arrival", "")

        flights.append(
            {
                "origin": origin,
                "originName": AIRPORT_NAMES.get(origin, origin),
                "airline": carrier,
                "airlineName": carrier,  # Kiwi doesn't always provide full names
                "price": str(flight.get("price", 0)),
                "currency": flight.get("currency", "CAD"),
                "departure": local_departure,
                "arrival": local_arrival,
                "duration": format_duration_seconds(flight.get("duration", {}).get("departure", 0)),
                "flightNumber": f"{carrier}{flight_no}",
            }
        )
    return flights


def format_duration_seconds(seconds: int) -> str:
    if not seconds:
        return ""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    if hours:
        parts.append(f"PT{hours}H")
    if minutes:
        if hours:
            return f"PT{hours}H{minutes}M"
        return f"PT{minutes}M"
    if hours:
        return f"PT{hours}H"
    return ""


async def fetch_flights_for(
    client: httpx.AsyncClient,
    api_key: str,
    origin: str,
    semaphore: asyncio.Semaphore,
) -> list[dict]:
    cached = _flight_cache.get(origin)
    if cached and time.time() - cached[0] < CACHE_TTL:
        return cached[1]

    async with semaphore:
        try:
            resp = await client.get(
                f"{KIWI_BASE}/v2/search",
                params={
                    "fly_from": origin,
                    "fly_to": "FLL",
                    "date_from": DATE_FROM,
                    "date_to": DATE_TO,
                    "adults": 1,
                    "max_stopovers": 0,
                    "curr": "CAD",
                    "limit": 100,
                    "one_for_city": 0,
                    "flight_type": "oneway",
                },
                headers={"apikey": api_key},
                timeout=30.0,
            )
        except httpx.TimeoutException:
            return []

        if resp.status_code != 200:
            return []

        flights = parse_kiwi_flights(origin, resp.json())
        _flight_cache[origin] = (time.time(), flights)
        return flights


class FlightResult(BaseModel):
    origin: str
    originName: str
    airline: str
    airlineName: str
    price: str
    currency: str
    departure: str
    arrival: str
    duration: str
    flightNumber: str


class FlightsResponse(BaseModel):
    flights: list[FlightResult]
    airports: list[dict]
    dates: list[str]
    searchedAt: str


@app.get("/api/flights", response_model=FlightsResponse)
async def get_flights():
    api_key = get_api_key()

    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(5)

        tasks = [
            fetch_flights_for(client, api_key, airport["code"], semaphore)
            for airport in AIRPORTS
        ]

        results = await asyncio.gather(*tasks)

    all_flights = [flight for batch in results for flight in batch]
    all_flights.sort(key=lambda f: float(f["price"]))

    return FlightsResponse(
        flights=all_flights,
        airports=AIRPORTS,
        dates=DATES,
        searchedAt=date.today().isoformat(),
    )


@app.get("/api/airports")
async def get_airports():
    return AIRPORTS


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
