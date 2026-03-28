import { ref } from 'vue'
import type { Flight, Airport, FlightsResponse, CheapestReturnsResponse } from '@/types'

const flights = ref<Flight[]>([])
const airports = ref<Airport[]>([])
const dates = ref<string[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const cheapestReturns = ref<Record<string, string | null>>({})
const cheapestReturnsLoading = ref(false)

export function useFlights() {
  async function fetchFlights() {
    loading.value = true
    error.value = null

    try {
      const resp = await fetch('/api/flights')
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}))
        throw new Error(body.detail || `Request failed with status ${resp.status}`)
      }
      const data: FlightsResponse = await resp.json()
      flights.value = data.flights
      airports.value = data.airports
      dates.value = data.dates
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch flights'
    } finally {
      loading.value = false
    }
  }

  async function fetchCheapestReturns() {
    cheapestReturnsLoading.value = true
    try {
      const resp = await fetch('/api/cheapest-returns')
      if (!resp.ok) return
      const data: CheapestReturnsResponse = await resp.json()
      cheapestReturns.value = data.cheapestReturns
    } catch {
      // silently fail -- round trip column just won't show prices
    } finally {
      cheapestReturnsLoading.value = false
    }
  }

  return { flights, airports, dates, loading, error, fetchFlights,
           cheapestReturns, cheapestReturnsLoading, fetchCheapestReturns }
}
