<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useFlights } from '@/composables/useFlights'
import FlightFilters from '@/components/FlightFilters.vue'
import FlightTable from '@/components/FlightTable.vue'
import type { SortField, Flight } from '@/types'

const { flights, airports, dates, loading, error, fetchFlights } = useFlights()

const selectedAirports = ref<Set<string>>(new Set())
const selectedDates = ref<Set<string>>(new Set())
const sortField = ref<SortField>('price')

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
</script>

<template>
  <div class="app">
    <header>
      <h1>Direct Flights to Fort Lauderdale (FLL)</h1>
      <p class="subtitle">
        From airports within 7 hours of Montreal &middot; Nov 11&ndash;15, 2026 &middot; Prices in CAD
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

    <div v-if="loading" class="status loading">
      <div class="spinner"></div>
      Searching for direct flights...
    </div>

    <div v-else-if="error" class="status error">
      {{ error }}
    </div>

    <template v-else>
      <p class="result-count">{{ resultCount }} flight{{ resultCount !== 1 ? 's' : '' }} found</p>
      <FlightTable :flights="filteredFlights" :cheapestByAirport="cheapestByAirport" />
    </template>

    <footer>
      <p>
        Flight data from Amadeus API (test environment &mdash; prices may be synthetic).
        Cheapest flights per airport highlighted in green.
      </p>
    </footer>
  </div>
</template>

<style>
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  color: #222;
  background: #f0f2f5;
  line-height: 1.5;
}

.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem 1rem;
}

header {
  text-align: center;
  margin-bottom: 1.5rem;
}

header h1 {
  font-size: 1.75rem;
  color: #1a3a5c;
  margin-bottom: 0.25rem;
}

.subtitle {
  color: #666;
  font-size: 0.95rem;
}

.result-count {
  margin: 1rem 0 0.5rem;
  font-size: 0.9rem;
  color: #555;
}

.status {
  text-align: center;
  padding: 3rem 1rem;
  font-size: 1.1rem;
}

.status.loading {
  color: #555;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.status.error {
  color: #c62828;
  background: #fce4ec;
  border-radius: 8px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e0e0e0;
  border-top-color: #1a3a5c;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

footer {
  margin-top: 2rem;
  text-align: center;
  font-size: 0.8rem;
  color: #999;
}
</style>
