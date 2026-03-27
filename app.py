import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import date

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fast_flights import FlightData, Passengers, create_filter
from fast_flights.core import get_flights_from_filter

app = FastAPI(title="Direct Flight Finder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

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

DATES = ["2026-11-11", "2026-11-12", "2026-11-13", "2026-11-14", "2026-11-15"]

AIRPORT_NAMES = {a["code"]: a["name"] for a in AIRPORTS}

# Cache: (origin, date) -> (timestamp, results)
_flight_cache: dict[tuple[str, str], tuple[float, list]] = {}
CACHE_TTL = 900  # 15 minutes

_executor = ThreadPoolExecutor(max_workers=5)


def search_flights(origin: str, departure_date: str) -> list[dict]:
    """Search Google Flights for direct flights from origin to FLL on a given date."""
    cache_key = (origin, departure_date)
    cached = _flight_cache.get(cache_key)
    if cached and time.time() - cached[0] < CACHE_TTL:
        return cached[1]

    try:
        tfs = create_filter(
            flight_data=[
                FlightData(
                    date=departure_date,
                    from_airport=origin,
                    to_airport="FLL",
                )
            ],
            trip="one-way",
            passengers=Passengers(adults=1),
            seat="economy",
            max_stops=0,
        )

        result = get_flights_from_filter(tfs, currency="CAD")

        flights = []
        for f in result.flights:
            if f.stops > 0:
                continue
            flights.append(
                {
                    "origin": origin,
                    "originName": AIRPORT_NAMES.get(origin, origin),
                    "airline": f.name,
                    "airlineName": f.name,
                    "price": f.price.replace("CA$", "").replace("$", "").replace(",", "").strip() if f.price else "0",
                    "currency": "CAD",
                    "departure": f.departure,
                    "arrival": f.arrival,
                    "duration": f.duration,
                    "flightNumber": f.name,
                }
            )

        _flight_cache[cache_key] = (time.time(), flights)
        return flights

    except Exception as e:
        print(f"Error searching {origin} on {departure_date}: {e}")
        return []


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
async def get_flights_endpoint():
    loop = asyncio.get_event_loop()

    tasks = [
        loop.run_in_executor(_executor, search_flights, airport["code"], d)
        for airport in AIRPORTS
        for d in DATES
    ]

    results = await asyncio.gather(*tasks)

    all_flights = [flight for batch in results for flight in batch]

    # Sort by price, handling non-numeric gracefully
    def sort_key(f: dict) -> float:
        try:
            return float(f["price"])
        except (ValueError, TypeError):
            return float("inf")

    all_flights.sort(key=sort_key)

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
