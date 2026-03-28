export interface Flight {
  origin: string
  originName: string
  airline: string
  airlineName: string
  price: string
  currency: string
  departure: string
  arrival: string
  duration: string
  flightNumber: string
  buyLink?: string
  source?: string
}

export interface ReturnFlight {
  origin: string
  originName: string
  destination: string
  destinationName: string
  airline: string
  airlineName: string
  price: string
  currency: string
  departure: string
  arrival: string
  duration: string
  flightNumber: string
  buyLink?: string
  source?: string
}

export interface ReturnFlightsResponse {
  flights: ReturnFlight[]
  date: string
  destination: string
}

export interface Airport {
  code: string
  name: string
  drive: string
}

export interface FlightsResponse {
  flights: Flight[]
  airports: Airport[]
  dates: string[]
  searchedAt: string
}

export type SortField = 'price' | 'departure' | 'origin' | 'airline'
