import asyncio
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fast_flights import FlightData, Passengers, create_filter
from fast_flights.core import get_flights_from_filter

app = FastAPI(title="Direct Flight Finder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

# Year for the search dates
SEARCH_YEAR = 2026


def parse_flight_time(time_str: str, search_date: str) -> str:
    """Parse '6:15 PM on Thu, Nov 12' into ISO format '2026-11-12T18:15:00'.

    Falls back to the search_date if parsing fails.
    """
    # Pattern: "6:15 PM on Thu, Nov 12"
    match = re.match(
        r"(\d{1,2}):(\d{2})\s*(AM|PM)\s+on\s+\w+,\s+(\w+)\s+(\d{1,2})",
        time_str.strip(),
    )
    if not match:
        return f"{search_date}T00:00:00"

    hour, minute, ampm, month_str, day = match.groups()
    hour = int(hour)
    minute = int(minute)
    day = int(day)

    if ampm == "PM" and hour != 12:
        hour += 12
    elif ampm == "AM" and hour == 12:
        hour = 0

    month_map = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
        "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
    }
    month = month_map.get(month_str, 11)

    return f"{SEARCH_YEAR}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:00"


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
        seen = set()
        for f in result.flights:
            if f.stops > 0:
                continue

            price_str = f.price.replace("CA$", "").replace("$", "").replace(",", "").strip() if f.price else "0"
            departure_iso = parse_flight_time(f.departure, departure_date)
            arrival_iso = parse_flight_time(f.arrival, departure_date)

            # Deduplicate by origin + airline + departure time + price
            dedup_key = (origin, f.name, departure_iso, price_str)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            flights.append(
                {
                    "origin": origin,
                    "originName": AIRPORT_NAMES.get(origin, origin),
                    "airline": f.name,
                    "airlineName": f.name,
                    "price": price_str,
                    "currency": "CAD",
                    "departure": departure_iso,
                    "arrival": arrival_iso,
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
