# Direct Flight Finder

Find direct flights to Fort Lauderdale (FLL) from airports within a 7-hour drive of Montreal, with prices in Canadian dollars.

No API keys or accounts needed — uses [fast-flights](https://pypi.org/project/fast-flights/) to get real-time data from Google Flights.

## Features

- Searches **13 airports** within a 7-hour drive of Montreal for non-stop flights to FLL
- Prices displayed in **Canadian dollars (CAD)**
- Dates: **November 11–15, 2026** (up to 4 days before Nov 15)
- Client-side **filtering** by airport and date
- **Sorting** by price, departure time, airport, or airline
- Cheapest flight per airport highlighted in green
- 15-minute result cache to avoid repeated scraping
- Parallel search across all airport/date combinations

## Airports searched

| Code | Airport | Drive from Montreal |
|------|---------|-------------------|
| YUL | Montreal Trudeau | 0 min |
| PBG | Plattsburgh NY | ~1 hr |
| BTV | Burlington VT | ~1.5 hr |
| YOW | Ottawa | ~2 hr |
| YQB | Quebec City | ~2.5 hr |
| ALB | Albany NY | ~3.5 hr |
| SYR | Syracuse NY | ~4 hr |
| ROC | Rochester NY | ~5 hr |
| PWM | Portland ME | ~5 hr |
| YYZ | Toronto Pearson | ~5.5 hr |
| BGM | Binghamton NY | ~5.5 hr |
| YKF | Waterloo ON | ~6 hr |
| BUF | Buffalo NY | ~6.5 hr |

## Prerequisites

- Python 3.11+
- Node.js 18+
- [pnpm](https://pnpm.io/)

## Setup

### Backend

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

The API runs on http://localhost:8000.

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Open http://localhost:5173 in your browser.

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/flights` | Search all airports/dates and return sorted results |
| `GET /api/airports` | List of airports with drive times |

## Tech stack

- **Backend**: Python [FastAPI](https://fastapi.tiangolo.com/) + [fast-flights](https://pypi.org/project/fast-flights/) (Google Flights scraper — no API key needed)
- **Frontend**: [Vue 3](https://vuejs.org/) + TypeScript + [Vite](https://vite.dev/) (pnpm)
