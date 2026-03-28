<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useFlights } from '@/composables/useFlights'
import FlightFilters from '@/components/FlightFilters.vue'
import FlightTable from '@/components/FlightTable.vue'
import ReturnFlightsModal from '@/components/ReturnFlightsModal.vue'
import FavoriteCombos from '@/components/FavoriteCombos.vue'
import type { SortField, Flight, ReturnFlight, FavoriteCombo } from '@/types'

const { flights, airports, dates, loading, error, progress, progressTotal,
        fetchFlights, cheapestReturns, cheapestReturnsLoading, fetchCheapestReturns } = useFlights()

const darkMode = ref(localStorage.getItem('darkMode') === 'true')

watch(darkMode, (val) => {
  document.documentElement.classList.toggle('dark', val)
  localStorage.setItem('darkMode', String(val))
}, { immediate: true })

// Favorites
const favorites = ref<FavoriteCombo[]>(JSON.parse(localStorage.getItem('favorites') || '[]'))
const currentFavPrices = ref<Record<string, { outbound: string; ret: string } | null>>({})

function saveFavorites() {
  localStorage.setItem('favorites', JSON.stringify(favorites.value))
}

function saveCombo(outbound: Flight, returnFlight: ReturnFlight, returnDate: string) {
  const total = (parseFloat(outbound.price) + parseFloat(returnFlight.price)).toFixed(2)
  const id = `${outbound.origin}-${outbound.departure}-${outbound.airline}-${returnFlight.departure}-${returnFlight.airline}`

  if (favorites.value.some((f) => f.id === id)) return

  favorites.value.push({
    id,
    outbound: {
      origin: outbound.origin,
      originName: outbound.originName,
      airline: outbound.airlineName,
      departure: outbound.departure,
      arrival: outbound.arrival,
      duration: outbound.duration,
      price: outbound.price,
      buyLink: outbound.buyLink,
    },
    returnFlight: {
      airline: returnFlight.airlineName,
      departure: returnFlight.departure,
      arrival: returnFlight.arrival,
      duration: returnFlight.duration,
      price: returnFlight.price,
      buyLink: returnFlight.buyLink,
    },
    returnDate,
    savedTotal: total,
    savedAt: new Date().toISOString(),
  })
  saveFavorites()
  refreshFavPrices()
}

function removeFavorite(id: string) {
  favorites.value = favorites.value.filter((f) => f.id !== id)
  saveFavorites()
}

async function refreshFavPrices() {
  for (const fav of favorites.value) {
    currentFavPrices.value[fav.id] = null
    try {
      const outDate = fav.outbound.departure.slice(0, 10)
      const [outResp, retResp] = await Promise.all([
        fetch(`/api/flights`),
        fetch(`/api/return-flights?destination=${fav.outbound.origin}`),
      ])
      if (!outResp.ok || !retResp.ok) continue

      const outData = await outResp.json()
      const retData = await retResp.json()

      const matchOut = outData.flights.find(
        (f: Flight) =>
          f.origin === fav.outbound.origin &&
          f.airlineName === fav.outbound.airline &&
          f.departure === fav.outbound.departure
      )
      const matchRet = retData.flights.find(
        (f: ReturnFlight) =>
          f.airlineName === fav.returnFlight.airline &&
          f.departure === fav.returnFlight.departure
      )

      if (matchOut && matchRet) {
        currentFavPrices.value[fav.id] = {
          outbound: matchOut.price,
          ret: matchRet.price,
        }
      }
    } catch {
      // keep as null
    }
  }
}

const selectedAirports = ref<Set<string>>(new Set())
const selectedDates = ref<Set<string>>(new Set())
const sortField = ref<SortField>('price')

const showReturnModal = ref(false)
const returnFlights = ref<ReturnFlight[]>([])
const returnLoading = ref(false)
const returnDestination = ref('')
const returnDestinationName = ref('')
const returnDate = ref('')
const selectedOutboundFlight = ref<Flight | null>(null)

// Initialize filters when airports arrive via SSE
watch(airports, (val) => {
  if (val.length > 0 && selectedAirports.value.size === 0) {
    selectedAirports.value = new Set(val.map((a) => a.code))
  }
})
watch(dates, (val) => {
  if (val.length > 0 && selectedDates.value.size === 0) {
    selectedDates.value = new Set(val)
  }
})

onMounted(() => {
  fetchFlights().then(() => {
    if (favorites.value.length > 0) refreshFavPrices()
  })
  fetchCheapestReturns()
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
    case 'roundTrip': {
      const aRet = cheapestReturns.value[a.origin]
      const bRet = cheapestReturns.value[b.origin]
      const aTotal = aRet ? parseFloat(a.price) + parseFloat(aRet.price) : Infinity
      const bTotal = bRet ? parseFloat(b.price) + parseFloat(bRet.price) : Infinity
      return aTotal - bTotal
    }
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
  selectedOutboundFlight.value = flight
  returnDestination.value = flight.origin
  returnDestinationName.value = flight.originName
  returnDate.value = '2026-11-22'

  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 20000)
  try {
    const resp = await fetch(`/api/return-flights?destination=${flight.origin}`, {
      signal: controller.signal,
    })
    if (!resp.ok) throw new Error('Failed to fetch return flights')
    const data = await resp.json()
    returnFlights.value = data.flights
    returnDate.value = data.date
  } catch {
    returnFlights.value = []
  } finally {
    clearTimeout(timeout)
    returnLoading.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-[1200px] px-4 py-6">
    <header class="relative mb-6 text-center">
      <button
        @click="darkMode = !darkMode"
        class="absolute right-0 top-0 cursor-pointer rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200"
      >
        {{ darkMode ? 'Light' : 'Dark' }}
      </button>
      <h1 class="mb-1 text-[1.75rem] font-bold text-[#1a3a5c] dark:text-blue-300">Direct Flights to Fort Lauderdale (FLL)</h1>
      <p class="text-[0.95rem] text-[#666] dark:text-slate-400">
        From airports within 7 hours of Montreal &middot; Nov 11&ndash;14, 2026 &middot; Prices in CAD
      </p>
    </header>

    <FavoriteCombos
      :favorites="favorites"
      :currentPrices="currentFavPrices"
      @remove="removeFavorite"
    />

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

    <div v-if="error && !loading && filteredFlights.length === 0" class="rounded-lg bg-[#fce4ec] px-4 py-12 text-center text-lg text-[#c62828] dark:bg-red-900/30 dark:text-red-400">
      {{ error }}
    </div>

    <template v-else>
      <div v-if="loading" class="mt-4 mb-3">
        <div class="flex items-center gap-3 text-sm text-[#555] dark:text-slate-400">
          <div class="size-4 animate-spin rounded-full border-2 border-[#e0e0e0] border-t-[#1a3a5c] dark:border-slate-600 dark:border-t-blue-400"></div>
          <span>Searching... {{ progress }}/{{ progressTotal }} routes</span>
        </div>
        <div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-slate-700">
          <div
            class="h-full rounded-full bg-[#1a3a5c] transition-all duration-300 dark:bg-blue-500"
            :style="{ width: progressTotal ? `${(progress / progressTotal) * 100}%` : '0%' }"
          ></div>
        </div>
      </div>
      <p v-if="!loading || filteredFlights.length > 0" class="mt-4 mb-2 text-sm text-[#555] dark:text-slate-400">
        {{ resultCount }} flight{{ resultCount !== 1 ? 's' : '' }} found{{ loading ? ' so far' : '' }}
      </p>
      <p class="mt-1 mb-4 text-xs text-[#888] dark:text-slate-500">Click a flight to see return options from FLL on Nov 22</p>
      <FlightTable v-if="filteredFlights.length > 0" :flights="filteredFlights" :cheapestByAirport="cheapestByAirport" :cheapestReturns="cheapestReturns" :cheapestReturnsLoading="cheapestReturnsLoading" @select-flight="onSelectFlight" />
      <div v-else-if="loading" class="py-8 text-center text-[#888] dark:text-slate-500">
        Flights will appear here as they are found...
      </div>
    </template>

    <ReturnFlightsModal
      v-if="showReturnModal"
      :flights="returnFlights"
      :outboundFlight="selectedOutboundFlight!"
      :destination="returnDestination"
      :destinationName="returnDestinationName"
      :date="returnDate"
      :loading="returnLoading"
      @close="showReturnModal = false"
      @save-combo="saveCombo"
    />

    <footer class="mt-8 text-center text-xs text-[#999] dark:text-slate-500">
      <p>
        Flight data from Amadeus API (test environment &mdash; prices may be synthetic).
        Cheapest flights per airport highlighted in green.
      </p>
    </footer>
  </div>
</template>
