import asyncio
import os
import time
from datetime import date

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

AMADEUS_BASE = "https://test.api.amadeus.com"

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

AIRLINES = {
    "AC": "Air Canada",
    "WS": "WestJet",
    "TS": "Air Transat",
    "F8": "Flair Airlines",
    "PD": "Porter Airlines",
    "NK": "Spirit Airlines",
    "B6": "JetBlue",
    "AA": "American Airlines",
    "DL": "Delta Air Lines",
    "UA": "United Airlines",
    "WN": "Southwest Airlines",
    "G4": "Allegiant Air",
    "SY": "Sun Country Airlines",
}

AIRPORT_NAMES = {a["code"]: a["name"] for a in AIRPORTS}

# Token cache
_token_cache: dict = {"token": None, "expires_at": 0.0}

# Flight results cache: (origin, date) -> (timestamp, results)
_flight_cache: dict[tuple[str, str], tuple[float, list]] = {}
CACHE_TTL = 900  # 15 minutes


async def get_amadeus_token(client: httpx.AsyncClient) -> str:
    if time.time() < _token_cache["expires_at"]:
        return _token_cache["token"]

    api_key = os.environ.get("AMADEUS_API_KEY", "")
    api_secret = os.environ.get("AMADEUS_API_SECRET", "")
    if not api_key or not api_secret:
        raise HTTPException(
            status_code=500,
            detail="Amadeus API credentials not configured. Set AMADEUS_API_KEY and AMADEUS_API_SECRET in .env",
        )

    resp = await client.post(
        f"{AMADEUS_BASE}/v1/security/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": api_secret,
        },
    )

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to authenticate with Amadeus API")

    data = resp.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data["expires_in"] - 60
    return _token_cache["token"]


def parse_flight_offers(origin: str, raw_data: dict) -> list[dict]:
    flights = []
    for offer in raw_data.get("data", []):
        price = offer.get("price", {})
        for itinerary in offer.get("itineraries", []):
            segments = itinerary.get("segments", [])
            if len(segments) != 1:
                continue  # skip non-direct
            seg = segments[0]
            carrier = seg.get("carrierCode", "")
            flights.append(
                {
                    "origin": origin,
                    "originName": AIRPORT_NAMES.get(origin, origin),
                    "airline": carrier,
                    "airlineName": AIRLINES.get(carrier, carrier),
                    "price": price.get("grandTotal", price.get("total", "0")),
                    "currency": price.get("currency", "CAD"),
                    "departure": seg.get("departure", {}).get("at", ""),
                    "arrival": seg.get("arrival", {}).get("at", ""),
                    "duration": itinerary.get("duration", ""),
                    "flightNumber": f"{carrier}{seg.get('number', '')}",
                }
            )
    return flights


async def fetch_flights_for(
    client: httpx.AsyncClient,
    token: str,
    origin: str,
    departure_date: str,
    semaphore: asyncio.Semaphore,
) -> list[dict]:
    cache_key = (origin, departure_date)
    cached = _flight_cache.get(cache_key)
    if cached and time.time() - cached[0] < CACHE_TTL:
        return cached[1]

    async with semaphore:
        try:
            resp = await client.get(
                f"{AMADEUS_BASE}/v2/shopping/flight-offers",
                params={
                    "originLocationCode": origin,
                    "destinationLocationCode": "FLL",
                    "departureDate": departure_date,
                    "adults": 1,
                    "nonStop": "true",
                    "currencyCode": "CAD",
                    "max": 50,
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0,
            )
        except httpx.TimeoutException:
            return []

        if resp.status_code != 200:
            return []

        flights = parse_flight_offers(origin, resp.json())
        _flight_cache[cache_key] = (time.time(), flights)
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
    async with httpx.AsyncClient() as client:
        token = await get_amadeus_token(client)
        semaphore = asyncio.Semaphore(5)

        tasks = [
            fetch_flights_for(client, token, airport["code"], d, semaphore)
            for airport in AIRPORTS
            for d in DATES
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
