import { ref } from 'vue'
import type { Flight, Airport, FlightsResponse, CheapestReturnsResponse, CheapestReturnFlight } from '@/types'

const flights = ref<Flight[]>([])
const airports = ref<Airport[]>([])
const dates = ref<string[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const progress = ref(0)
const progressTotal = ref(0)
const cheapestReturns = ref<Record<string, CheapestReturnFlight | null>>({})
const cheapestReturnsLoading = ref(false)

export function useFlights() {
  async function fetchFlightsClassic() {
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

  function fetchFlights(): Promise<void> {
    loading.value = true
    error.value = null
    flights.value = []
    progress.value = 0
    progressTotal.value = 0

    return new Promise((resolve) => {
      let receivedAny = false

      const evtSource = new EventSource('/api/flights/stream')

      evtSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          receivedAny = true

          if (data.type === 'init') {
            airports.value = data.airports
            dates.value = data.dates
          } else if (data.type === 'flights') {
            flights.value = [...flights.value, ...data.flights]
            progress.value = data.progress
            progressTotal.value = data.total
          } else if (data.type === 'done') {
            evtSource.close()
            loading.value = false
            resolve()
          }
        } catch {
          // ignore parse errors
        }
      }

      evtSource.onerror = () => {
        evtSource.close()
        if (!receivedAny) {
          // SSE not supported or failed to connect — fall back to classic fetch
          console.log('SSE failed, falling back to /api/flights')
          fetchFlightsClassic().then(resolve)
        } else {
          // Stream was interrupted mid-way
          loading.value = false
          resolve()
        }
      }
    })
  }

  async function fetchCheapestReturns() {
    cheapestReturnsLoading.value = true
    try {
      const resp = await fetch('/api/cheapest-returns')
      if (!resp.ok) return
      const data: CheapestReturnsResponse = await resp.json()
      cheapestReturns.value = data.cheapestReturns
    } catch {
      // silently fail
    } finally {
      cheapestReturnsLoading.value = false
    }
  }

  return { flights, airports, dates, loading, error, progress, progressTotal,
           fetchFlights, cheapestReturns, cheapestReturnsLoading, fetchCheapestReturns }
}
