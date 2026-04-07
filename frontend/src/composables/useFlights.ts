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
  async function fetchAirportsAndDates() {
    const metaResp = await fetch('/api/airports')
    if (!metaResp.ok) throw new Error('Failed to fetch airport list')
    const meta = await metaResp.json()
    const airportList: Airport[] = Array.isArray(meta) ? meta : meta.airports
    const dateList: string[] = Array.isArray(meta) ? [] : (meta.dates || [])
    airports.value = airportList
    dates.value = dateList
    return { airportList, dateList }
  }

  async function fetchFlights(selectedAirports?: Set<string>, selectedDates?: Set<string>) {
    loading.value = true
    error.value = null
    flights.value = []
    progress.value = 0
    progressTotal.value = 0

    try {
      // Ensure airports/dates are loaded
      let airportList = airports.value
      if (airportList.length === 0) {
        const meta = await fetchAirportsAndDates()
        airportList = meta.airportList
      }

      // Filter to only selected airports
      const airportsToSearch = selectedAirports
        ? airportList.filter((a) => selectedAirports.has(a.code))
        : airportList

      // Build dates query param
      const datesParam = selectedDates && selectedDates.size > 0
        ? Array.from(selectedDates).join(',')
        : ''

      progressTotal.value = airportsToSearch.length

      // Fetch in batches of 3 to avoid overwhelming serverless functions
      const batchSize = 3
      for (let i = 0; i < airportsToSearch.length; i += batchSize) {
        const batch = airportsToSearch.slice(i, i + batchSize)
        const promises = batch.map(async (airport) => {
          const controller = new AbortController()
          const timeout = setTimeout(() => controller.abort(), 55000)
          try {
            const url = datesParam
              ? `/api/flights/airport?origin=${airport.code}&dates=${datesParam}`
              : `/api/flights/airport?origin=${airport.code}`
            const resp = await fetch(url, { signal: controller.signal })
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
           fetchFlights, fetchAirportsAndDates,
           cheapestReturns, cheapestReturnsLoading, fetchCheapestReturns }
}
