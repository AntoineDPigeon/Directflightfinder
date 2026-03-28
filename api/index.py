import asyncio
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
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
    {"code": "PBG", "name": "Plattsburgh NY", "drive": "~1 hr"},
    {"code": "BTV", "name": "Burlington VT", "drive": "~1.5 hr"},
    {"code": "YOW", "name": "Ottawa", "drive": "~2 hr"},
    {"code": "YQB", "name": "Quebec City", "drive": "~2.5 hr"},
    {"code": "ALB", "name": "Albany NY", "drive": "~3.5 hr"},
    {"code": "SYR", "name": "Syracuse NY", "drive": "~4 hr"},
    {"code": "MHT", "name": "Manchester NH", "drive": "~4.5 hr"},
    {"code": "BOS", "name": "Boston Logan", "drive": "~5 hr"},
    {"code": "ROC", "name": "Rochester NY", "drive": "~5 hr"},
    {"code": "PWM", "name": "Portland ME", "drive": "~5 hr"},
    {"code": "BDL", "name": "Hartford/Bradley CT", "drive": "~5 hr"},
    {"code": "SWF", "name": "Stewart/Newburgh NY", "drive": "~5.5 hr"},
    {"code": "ITH", "name": "Ithaca NY", "drive": "~5.5 hr"},
    {"code": "BGM", "name": "Binghamton NY", "drive": "~5.5 hr"},
    {"code": "YYZ", "name": "Toronto Pearson", "drive": "~5.5 hr"},
    {"code": "PVD", "name": "Providence RI", "drive": "~5.5 hr"},
    {"code": "HPN", "name": "Westchester County NY", "drive": "~6 hr"},
    {"code": "YKF", "name": "Waterloo ON", "drive": "~6 hr"},
    {"code": "YHM", "name": "Hamilton ON", "drive": "~6 hr"},
    {"code": "ELM", "name": "Elmira/Corning NY", "drive": "~6 hr"},
    {"code": "LGA", "name": "LaGuardia NY", "drive": "~6 hr"},
    {"code": "BUF", "name": "Buffalo NY", "drive": "~6.5 hr"},
    {"code": "EWR", "name": "Newark Liberty NJ", "drive": "~6.5 hr"},
]

DATES = ["2026-11-11", "2026-11-12", "2026-11-13", "2026-11-14"]

AIRPORT_NAMES = {a["code"]: a["name"] for a in AIRPORTS}

# Cache: (source, origin, destination, date) -> (timestamp, results)
_flight_cache: dict[tuple[str, str, str, str], tuple[float, list]] = {}
CACHE_TTL = 900  # 15 minutes

_executor = ThreadPoolExecutor(max_workers=5)

SEARCH_YEAR = 2026

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "google-flights-live-api.p.rapidapi.com"

# ---------------------------------------------------------------------------
# USD → CAD conversion via Bank of Canada
# ---------------------------------------------------------------------------

_usd_cad_rate: float | None = None
_usd_cad_fetched: float = 0


def get_usd_to_cad() -> float:
    """Fetch current USD→CAD rate from Bank of Canada. Cached for 6 hours."""
    global _usd_cad_rate, _usd_cad_fetched
    if _usd_cad_rate and time.time() - _usd_cad_fetched < 21600:
        return _usd_cad_rate

    try:
        resp = requests.get(
            "https://www.bankofcanada.ca/valet/observations/FXUSDCAD/json",
            params={"recent": 1},
            timeout=10,
        )
        obs = resp.json()["observations"][0]
        _usd_cad_rate = float(obs["FXUSDCAD"]["v"])
        _usd_cad_fetched = time.time()
        print(f"[fx] USD→CAD rate: {_usd_cad_rate}")
    except Exception as e:
        print(f"[fx] Failed to fetch rate: {e}")
        if not _usd_cad_rate:
            _usd_cad_rate = 1.39  # fallback
    return _usd_cad_rate


# ---------------------------------------------------------------------------
# Time parsing helper (for fast-flights responses)
# ---------------------------------------------------------------------------

def parse_flight_time(time_str: str, search_date: str) -> str:
    """Parse '6:15 PM on Thu, Nov 12' into ISO format '2026-11-12T18:15:00'."""
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


# ---------------------------------------------------------------------------
# Source 1: fast-flights (Google Flights scraper, no API key)
# ---------------------------------------------------------------------------

def search_fast_flights(origin: str, destination: str, departure_date: str) -> list[dict]:
    """Search via fast-flights (Google Flights scraper)."""
    cache_key = ("fast", origin, destination, departure_date)
    cached = _flight_cache.get(cache_key)
    if cached and time.time() - cached[0] < CACHE_TTL:
        return cached[1]

    try:
        tfs = create_filter(
            flight_data=[
                FlightData(
                    date=departure_date,
                    from_airport=origin,
                    to_airport=destination,
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

            dedup_key = (origin, f.name, departure_iso, price_str)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            flights.append(
                {
                    "origin": origin,
                    "originName": AIRPORT_NAMES.get(origin, origin),
                    "destination": destination,
                    "destinationName": AIRPORT_NAMES.get(destination, destination),
                    "airline": f.name,
                    "airlineName": f.name,
                    "price": price_str,
                    "currency": "CAD",
                    "departure": departure_iso,
                    "arrival": arrival_iso,
                    "duration": f.duration,
                    "flightNumber": f.name,
                    "buyLink": f"https://www.google.com/travel/flights?q=Flights%20to%20{destination}%20from%20{origin}%20on%20{departure_date}%20oneway",
                    "source": "google-flights",
                }
            )

        _flight_cache[cache_key] = (time.time(), flights)
        return flights

    except Exception as e:
        print(f"[fast-flights] Error {origin}->{destination} on {departure_date}: {e}")
        return []


# ---------------------------------------------------------------------------
# Source 2: RapidAPI Google Flights Live API
# ---------------------------------------------------------------------------

def search_rapidapi(origin: str, destination: str, departure_date: str) -> list[dict]:
    """Search via RapidAPI Google Flights Live API."""
    if not RAPIDAPI_KEY:
        return []

    cache_key = ("rapid", origin, destination, departure_date)
    cached = _flight_cache.get(cache_key)
    if cached and time.time() - cached[0] < CACHE_TTL:
        return cached[1]

    try:
        resp = requests.post(
            f"https://{RAPIDAPI_HOST}/api/google_flights/oneway/v1",
            headers={
                "Content-Type": "application/json",
                "x-rapidapi-host": RAPIDAPI_HOST,
                "x-rapidapi-key": RAPIDAPI_KEY,
            },
            json={
                "departure_date": departure_date,
                "from_airport": origin,
                "to_airport": destination,
            },
            timeout=15,
        )

        if resp.status_code != 200:
            print(f"[rapidapi] HTTP {resp.status_code} for {origin}->{destination}: {resp.text[:200]}")
            return []

        data = resp.json()
        if isinstance(data, dict):
            # Error response (e.g. rate limit)
            print(f"[rapidapi] Error for {origin}->{destination}: {data.get('message', str(data)[:200])}")
            return []

        flights = []
        for f in data:
            if f.get("stops", 0) > 0:
                continue

            usd_price = f.get("price_as_number", 0)
            cad_price = round(usd_price * get_usd_to_cad(), 2)
            price_str = str(cad_price)
            departure_iso = parse_flight_time(
                f.get("departure_description", ""), departure_date
            )
            arrival_iso = parse_flight_time(
                f.get("arrival_description", ""), departure_date
            )

            # Extract clean airline name (strip "Operated by..." text)
            airline_raw = f.get("airline", "")
            airline_name = airline_raw.split(" | ")[0].split(",")[0].strip()

            # Duration comes as "3 hr 24 min" — convert to ISO-ish
            duration_str = f.get("duration", "")
            dur_match = re.match(r"(\d+)\s*hr\s*(\d+)\s*min", duration_str)
            duration_iso = f"PT{dur_match.group(1)}H{dur_match.group(2)}M" if dur_match else duration_str

            flights.append(
                {
                    "origin": origin,
                    "originName": AIRPORT_NAMES.get(origin, origin),
                    "destination": destination,
                    "destinationName": AIRPORT_NAMES.get(destination, destination),
                    "airline": airline_name,
                    "airlineName": airline_name,
                    "price": price_str,
                    "currency": "CAD",
                    "departure": departure_iso,
                    "arrival": arrival_iso,
                    "duration": duration_iso,
                    "flightNumber": airline_name,
                    "buyLink": f.get("buy_link", ""),
                    "source": "rapidapi",
                }
            )

        _flight_cache[cache_key] = (time.time(), flights)
        return flights

    except Exception as e:
        print(f"[rapidapi] Error {origin}->{destination} on {departure_date}: {e}")
        return []


# ---------------------------------------------------------------------------
# Combined search with deduplication
# ---------------------------------------------------------------------------

def search_all_sources(origin: str, destination: str, departure_date: str) -> list[dict]:
    """Search both sources and deduplicate results."""
    fast = search_fast_flights(origin, destination, departure_date)
    rapid = search_rapidapi(origin, destination, departure_date)

    return deduplicate_flights(fast + rapid)


def deduplicate_flights(flights: list[dict]) -> list[dict]:
    """Deduplicate flights by airline + departure time, keeping the one with CAD currency preferred."""
    seen: dict[tuple, dict] = {}
    for f in flights:
        # Normalize airline name for matching
        airline_key = f["airline"].lower().strip()
        dep_key = f["departure"]
        key = (f["origin"], airline_key, dep_key)

        if key not in seen:
            seen[key] = f
        else:
            # Prefer CAD-priced result over USD
            existing = seen[key]
            if existing["currency"] == "USD" and f["currency"] == "CAD":
                seen[key] = f

    return list(seen.values())


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

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
    source: str = "google-flights"


class FlightsResponse(BaseModel):
    flights: list[FlightResult]
    airports: list[dict]
    dates: list[str]
    searchedAt: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/flights/stream")
async def stream_flights():
    """Stream flight results as Server-Sent Events as each search completes."""

    async def event_generator():
        yield f"data: {json.dumps({'type': 'init', 'airports': AIRPORTS, 'dates': DATES})}\n\n"

        queue: asyncio.Queue = asyncio.Queue()
        total = len(AIRPORTS) * len(DATES)

        async def run_search(origin: str, dest: str, d: str):
            loop = asyncio.get_event_loop()
            try:
                result = await loop.run_in_executor(
                    _executor, search_all_sources, origin, dest, d
                )
            except Exception:
                result = []
            await queue.put(result)

        # Launch all searches concurrently
        for airport in AIRPORTS:
            for d in DATES:
                asyncio.ensure_future(run_search(airport["code"], "FLL", d))

        for done_count in range(1, total + 1):
            flights = await queue.get()
            yield f"data: {json.dumps({'type': 'flights', 'flights': flights, 'progress': done_count, 'total': total})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'searchedAt': date.today().isoformat()})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/flights", response_model=FlightsResponse)
async def get_flights_endpoint():
    loop = asyncio.get_event_loop()

    tasks = [
        loop.run_in_executor(_executor, search_all_sources, airport["code"], "FLL", d)
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


@app.get("/api/flights/airport")
async def get_flights_for_airport(origin: str):
    """Search flights for a single airport across all dates."""
    valid_codes = {a["code"] for a in AIRPORTS}
    if origin not in valid_codes:
        raise HTTPException(status_code=400, detail=f"Unknown airport code: {origin}")

    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(_executor, search_all_sources, origin, "FLL", d)
        for d in DATES
    ]
    results = await asyncio.gather(*tasks)
    flights = [f for batch in results for f in batch]
    return {"flights": flights, "origin": origin}


RETURN_DATE = "2026-11-22"


@app.get("/api/return-flights")
async def get_return_flights(destination: str):
    """Search for direct return flights from FLL to a specific airport on Nov 22."""
    valid_codes = {a["code"] for a in AIRPORTS}
    if destination not in valid_codes:
        raise HTTPException(status_code=400, detail=f"Unknown airport code: {destination}")

    loop = asyncio.get_event_loop()
    flights = await loop.run_in_executor(
        _executor, search_all_sources, "FLL", destination, RETURN_DATE
    )

    def sort_key(f: dict) -> float:
        try:
            return float(f["price"])
        except (ValueError, TypeError):
            return float("inf")

    flights.sort(key=sort_key)
    return {"flights": flights, "date": RETURN_DATE, "destination": destination}


@app.get("/api/cheapest-returns")
async def get_cheapest_returns():
    """Return cheapest return flight price per airport (FLL -> each airport on Nov 22)."""
    loop = asyncio.get_event_loop()

    tasks = [
        loop.run_in_executor(_executor, search_fast_flights, "FLL", airport["code"], RETURN_DATE)
        for airport in AIRPORTS
    ]
    results = await asyncio.gather(*tasks)

    cheapest: dict[str, dict | None] = {}
    for airport, flights in zip(AIRPORTS, results):
        code = airport["code"]
        if not flights:
            cheapest[code] = None
            continue
        best = None
        best_price = float("inf")
        for f in flights:
            try:
                p = float(f["price"])
            except (ValueError, TypeError):
                continue
            if p < best_price:
                best_price = p
                best = f
        cheapest[code] = best

    return {"cheapestReturns": cheapest, "returnDate": RETURN_DATE}


@app.get("/api/airports")
async def get_airports():
    return {"airports": AIRPORTS, "dates": DATES}
