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
  async function fetchFlights() {
    loading.value = true
    error.value = null
    flights.value = []
    progress.value = 0
    progressTotal.value = 0

    try {
      // Get airports and dates
      const metaResp = await fetch('/api/airports')
      if (!metaResp.ok) throw new Error('Failed to fetch airport list')
      const meta = await metaResp.json()

      // Handle both formats: {airports, dates} or plain array
      const airportList: Airport[] = Array.isArray(meta) ? meta : meta.airports
      const dateList: string[] = Array.isArray(meta) ? [] : (meta.dates || [])
      airports.value = airportList
      dates.value = dateList

      // Fetch flights per airport in parallel — results appear as each completes
      progressTotal.value = airportList.length

      const promises = airportList.map(async (airport) => {
        const controller = new AbortController()
        const timeout = setTimeout(() => controller.abort(), 20000)
        try {
          const resp = await fetch(`/api/flights/airport?origin=${airport.code}`, {
            signal: controller.signal,
          })
          if (!resp.ok) return
          const data = await resp.json()
          flights.value = [...flights.value, ...data.flights]
        } catch {
          // skip failed or timed-out airport
        } finally {
          clearTimeout(timeout)
          progress.value++
        }
      })

      await Promise.all(promises)

      // Infer dates from flights if not provided by API
      if (dates.value.length === 0 && flights.value.length > 0) {
        const dateSet = new Set<string>()
        for (const f of flights.value) {
          dateSet.add(f.departure.slice(0, 10))
        }
        dates.value = [...dateSet].sort()
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch flights'
    } finally {
      loading.value = false
    }
  }

  async function fetchCheapestReturns() {
    cheapestReturnsLoading.value = true
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 60000)
    try {
      const resp = await fetch('/api/cheapest-returns', { signal: controller.signal })
      if (!resp.ok) return
      const data: CheapestReturnsResponse = await resp.json()
      cheapestReturns.value = data.cheapestReturns
    } catch {
      // silently fail
    } finally {
      clearTimeout(timeout)
      cheapestReturnsLoading.value = false
    }
  }

  return { flights, airports, dates, loading, error, progress, progressTotal,
           fetchFlights, cheapestReturns, cheapestReturnsLoading, fetchCheapestReturns }
}
