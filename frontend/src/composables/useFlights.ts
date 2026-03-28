import { ref } from 'vue'
import type { Flight, Airport, CheapestReturnsResponse, CheapestReturnFlight } from '@/types'

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
  function fetchFlights(): Promise<void> {
    loading.value = true
    error.value = null
    flights.value = []
    progress.value = 0
    progressTotal.value = 0

    return new Promise((resolve) => {
      const evtSource = new EventSource('/api/flights/stream')

      evtSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

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
        if (flights.value.length === 0) {
          error.value = 'Failed to fetch flights'
        }
        loading.value = false
        resolve()
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
