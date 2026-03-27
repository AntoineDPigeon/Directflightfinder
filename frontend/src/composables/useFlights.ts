import { ref } from 'vue'
import type { Flight, Airport, FlightsResponse } from '@/types'

const flights = ref<Flight[]>([])
const airports = ref<Airport[]>([])
const dates = ref<string[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

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

  return { flights, airports, dates, loading, error, fetchFlights }
}
