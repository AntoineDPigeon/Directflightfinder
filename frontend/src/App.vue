<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useFlights } from '@/composables/useFlights'
import FlightFilters from '@/components/FlightFilters.vue'
import FlightTable from '@/components/FlightTable.vue'
import ReturnFlightsModal from '@/components/ReturnFlightsModal.vue'
import type { SortField, Flight, ReturnFlight } from '@/types'

const { flights, airports, dates, loading, error, fetchFlights } = useFlights()

const selectedAirports = ref<Set<string>>(new Set())
const selectedDates = ref<Set<string>>(new Set())
const sortField = ref<SortField>('price')

const showReturnModal = ref(false)
const returnFlights = ref<ReturnFlight[]>([])
const returnLoading = ref(false)
const returnDestination = ref('')
const returnDestinationName = ref('')
const returnDate = ref('')

onMounted(async () => {
  await fetchFlights()
  selectedAirports.value = new Set(airports.value.map((a) => a.code))
  selectedDates.value = new Set(dates.value)
})

function toggleAirport(code: string) {
  const s = new Set(selectedAirports.value)
  if (s.has(code)) s.delete(code)
  else s.add(code)
  selectedAirports.value = s
}

function toggleDate(date: string) {
  const s = new Set(selectedDates.value)
  if (s.has(date)) s.delete(date)
  else s.add(date)
  selectedDates.value = s
}

function selectAllAirports() {
  selectedAirports.value = new Set(airports.value.map((a) => a.code))
}
function clearAllAirports() {
  selectedAirports.value = new Set()
}
function selectAllDates() {
  selectedDates.value = new Set(dates.value)
}
function clearAllDates() {
  selectedDates.value = new Set()
}

function getDateFromDeparture(departure: string): string {
  return departure.slice(0, 10)
}

function sortFlights(a: Flight, b: Flight): number {
  switch (sortField.value) {
    case 'price':
      return parseFloat(a.price) - parseFloat(b.price)
    case 'departure':
      return a.departure.localeCompare(b.departure)
    case 'origin':
      return a.origin.localeCompare(b.origin) || parseFloat(a.price) - parseFloat(b.price)
    case 'airline':
      return a.airlineName.localeCompare(b.airlineName) || parseFloat(a.price) - parseFloat(b.price)
    default:
      return 0
  }
}

const filteredFlights = computed(() => {
  return flights.value
    .filter(
      (f) =>
        selectedAirports.value.has(f.origin) &&
        selectedDates.value.has(getDateFromDeparture(f.departure))
    )
    .sort(sortFlights)
})

const cheapestByAirport = computed(() => {
  const map: Record<string, number> = {}
  for (const f of filteredFlights.value) {
    const p = parseFloat(f.price)
    if (!(f.origin in map) || p < map[f.origin]) {
      map[f.origin] = p
    }
  }
  return map
})

const resultCount = computed(() => filteredFlights.value.length)

async function onSelectFlight(flight: Flight) {
  showReturnModal.value = true
  returnLoading.value = true
  returnFlights.value = []
  returnDestination.value = flight.origin
  returnDestinationName.value = flight.originName

  try {
    const resp = await fetch(`/api/return-flights?destination=${flight.origin}`)
    if (!resp.ok) throw new Error('Failed to fetch return flights')
    const data = await resp.json()
    returnFlights.value = data.flights
    returnDate.value = data.date
  } catch {
    returnFlights.value = []
  } finally {
    returnLoading.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-[1200px] px-4 py-6">
    <header class="mb-6 text-center">
      <h1 class="mb-1 text-[1.75rem] font-bold text-[#1a3a5c]">Direct Flights to Fort Lauderdale (FLL)</h1>
      <p class="text-[0.95rem] text-[#666]">
        From airports within 7 hours of Montreal &middot; Nov 11&ndash;14, 2026 &middot; Prices in CAD
      </p>
    </header>

    <FlightFilters
      :airports="airports"
      :dates="dates"
      :selectedAirports="selectedAirports"
      :selectedDates="selectedDates"
      :sortField="sortField"
      @toggle-airport="toggleAirport"
      @toggle-date="toggleDate"
      @update-sort="sortField = $event"
      @select-all-airports="selectAllAirports"
      @clear-all-airports="clearAllAirports"
      @select-all-dates="selectAllDates"
      @clear-all-dates="clearAllDates"
    />

    <div v-if="loading" class="flex flex-col items-center gap-4 px-4 py-12 text-center text-lg text-[#555]">
      <div class="size-10 animate-spin rounded-full border-4 border-[#e0e0e0] border-t-[#1a3a5c]"></div>
      Searching for direct flights...
    </div>

    <div v-else-if="error" class="rounded-lg bg-[#fce4ec] px-4 py-12 text-center text-lg text-[#c62828]">
      {{ error }}
    </div>

    <template v-else>
      <p class="mt-4 mb-2 text-sm text-[#555]">{{ resultCount }} flight{{ resultCount !== 1 ? 's' : '' }} found</p>
      <p class="mt-1 mb-4 text-xs text-[#888]">Click a flight to see return options from FLL on Nov 22</p>
      <FlightTable :flights="filteredFlights" :cheapestByAirport="cheapestByAirport" @select-flight="onSelectFlight" />
    </template>

    <ReturnFlightsModal
      v-if="showReturnModal"
      :flights="returnFlights"
      :destination="returnDestination"
      :destinationName="returnDestinationName"
      :date="returnDate"
      :loading="returnLoading"
      @close="showReturnModal = false"
    />

    <footer class="mt-8 text-center text-xs text-[#999]">
      <p>
        Flight data from Amadeus API (test environment &mdash; prices may be synthetic).
        Cheapest flights per airport highlighted in green.
      </p>
    </footer>
  </div>
</template>
