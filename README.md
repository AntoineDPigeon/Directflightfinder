# Direct Flight Finder

Find direct flights to Fort Lauderdale (FLL) from airports within a 7-hour drive of Montreal, with prices in Canadian dollars.

No API keys or accounts needed — uses [fast-flights](https://pypi.org/project/fast-flights/) to get data from Google Flights.

## Airports searched

| Code | Airport | Drive from Montreal |
|------|---------|-------------------|
| YUL | Montreal Trudeau | 0 min |
| YOW | Ottawa | ~2 hr |
| YQB | Quebec City | ~2.5 hr |
| BTV | Burlington VT | ~1.5 hr |
| PBG | Plattsburgh NY | ~1 hr |
| SYR | Syracuse NY | ~4 hr |
| ALB | Albany NY | ~3.5 hr |
| YYZ | Toronto Pearson | ~5.5 hr |
| ROC | Rochester NY | ~5 hr |
| PWM | Portland ME | ~5 hr |
| BGM | Binghamton NY | ~5.5 hr |
| YKF | Waterloo ON | ~6 hr |
| BUF | Buffalo NY | ~6.5 hr |

## Setup

### 1. Backend

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

The API runs on http://localhost:8000.

### 2. Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Open http://localhost:5173 in your browser.

## Tech stack

- **Backend**: Python FastAPI + fast-flights (Google Flights scraper, no API key needed)
- **Frontend**: Vue 3 + TypeScript + Vite (pnpm)
