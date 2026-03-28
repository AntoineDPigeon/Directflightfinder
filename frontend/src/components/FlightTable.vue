<script setup lang="ts">
import type { Flight, CheapestReturnFlight } from '@/types'

const props = defineProps<{
  flights: Flight[]
  cheapestByAirport: Record<string, number>
  cheapestReturns: Record<string, CheapestReturnFlight | null>
  cheapestReturnsLoading: boolean
}>()

const emit = defineEmits<{
  selectFlight: [flight: Flight]
}>()

function formatPrice(price: string, currency: string = 'CAD'): string {
  const num = parseFloat(price)
  return new Intl.NumberFormat('en-CA', { style: 'currency', currency }).format(num)
}

function formatDate(isoStr: string): string {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return d.toLocaleDateString('en-CA', { weekday: 'short', month: 'short', day: 'numeric' })
}

function formatTime(isoStr: string): string {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return d.toLocaleTimeString('en-CA', { hour: '2-digit', minute: '2-digit', hour12: false })
}

function formatDuration(iso: string): string {
  if (!iso) return ''
  const match = iso.match(/PT(?:(\d+)H)?(?:(\d+)M)?/)
  if (!match) return iso
  const h = match[1] ? `${match[1]}h` : ''
  const m = match[2] ? ` ${match[2]}m` : ''
  return `${h}${m}`.trim()
}

function isCheapest(flight: Flight, cheapestByAirport: Record<string, number>): boolean {
  return parseFloat(flight.price) === cheapestByAirport[flight.origin]
}

function getReturn(flight: Flight): CheapestReturnFlight | null {
  return props.cheapestReturns[flight.origin] ?? null
}

function roundTripPrice(flight: Flight): number | null {
  const ret = getReturn(flight)
  if (!ret) return null
  return parseFloat(flight.price) + parseFloat(ret.price)
}
</script>

<template>
  <div class="overflow-x-auto">
    <table class="w-full border-collapse text-sm">
      <thead class="bg-[#1a3a5c] text-white dark:bg-slate-900">
        <tr>
          <th class="px-2.5 py-3 text-left text-xs font-semibold uppercase tracking-wide">Origin</th>
          <th class="px-2.5 py-3 text-left text-xs font-semibold uppercase tracking-wide">Date</th>
          <th class="px-2.5 py-3 text-left text-xs font-semibold uppercase tracking-wide">Airline</th>
          <th class="px-2.5 py-3 text-left text-xs font-semibold uppercase tracking-wide">Flight</th>
          <th class="px-2.5 py-3 text-left text-xs font-semibold uppercase tracking-wide">Departure</th>
          <th class="px-2.5 py-3 text-left text-xs font-semibold uppercase tracking-wide">Arrival</th>
          <th class="px-2.5 py-3 text-left text-xs font-semibold uppercase tracking-wide">Duration</th>
          <th class="px-2.5 py-3 text-right text-xs font-bold uppercase tracking-wide whitespace-nowrap">Outbound</th>
          <th class="px-2.5 py-3 text-right text-xs font-bold uppercase tracking-wide whitespace-nowrap">Round Trip</th>
          <th class="px-2.5 py-3 text-center text-xs font-semibold uppercase tracking-wide"></th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(flight, i) in flights" :key="i">
          <!-- Outbound row -->
          <tr
            class="cursor-pointer border-b-0 even:bg-[#f9fafb] hover:bg-[#eef3f8] dark:even:bg-slate-800 dark:hover:bg-slate-700"
            :class="{ '!bg-[#e8f5e9] dark:!bg-green-900/40 font-medium': isCheapest(flight, cheapestByAirport) }"
            @click="emit('selectFlight', flight)"
          >
            <td class="px-2.5 pt-2.5 pb-0.5">
              <strong>{{ flight.origin }}</strong>
              <span class="block text-xs text-[#777] dark:text-slate-400">{{ flight.originName }}</span>
            </td>
            <td class="px-2.5 pt-2.5 pb-0.5">{{ formatDate(flight.departure) }}</td>
            <td class="px-2.5 pt-2.5 pb-0.5">{{ flight.airlineName }}</td>
            <td class="px-2.5 pt-2.5 pb-0.5">{{ flight.flightNumber }}</td>
            <td class="px-2.5 pt-2.5 pb-0.5">{{ formatTime(flight.departure) }}</td>
            <td class="px-2.5 pt-2.5 pb-0.5">{{ formatTime(flight.arrival) }}</td>
            <td class="px-2.5 pt-2.5 pb-0.5">{{ formatDuration(flight.duration) }}</td>
            <td class="px-2.5 pt-2.5 pb-0.5 text-right font-bold whitespace-nowrap">{{ formatPrice(flight.price) }}</td>
            <td class="px-2.5 pt-2.5 pb-0.5 text-right font-bold whitespace-nowrap text-[#1a3a5c] dark:text-blue-300" rowspan="2">
              <span v-if="cheapestReturnsLoading" class="inline-block size-3 animate-spin rounded-full border-2 border-gray-300 border-t-[#1a3a5c] dark:border-slate-600 dark:border-t-blue-400"></span>
              <template v-else-if="roundTripPrice(flight) !== null">
                {{ formatPrice(roundTripPrice(flight)!.toFixed(2)) }}
              </template>
              <span v-else class="text-[#aaa] dark:text-slate-600">--</span>
            </td>
            <td class="px-2.5 pt-2.5 pb-0.5 text-center" rowspan="2">
              <a
                v-if="flight.buyLink"
                :href="flight.buyLink"
                target="_blank"
                rel="noopener"
                class="inline-block rounded bg-[#0066cc] px-3 py-1 text-xs font-semibold text-white no-underline hover:bg-[#004499] dark:bg-blue-600 dark:hover:bg-blue-500"
                @click.stop
              >Book</a>
            </td>
          </tr>
          <!-- Return flight sub-row -->
          <tr
            class="cursor-pointer border-b border-[#e8e8e8] dark:border-slate-700"
            :class="{
              'bg-[#f9fafb] dark:bg-slate-800': i % 2 === 1,
              '!bg-[#e8f5e9] dark:!bg-green-900/40': isCheapest(flight, cheapestByAirport)
            }"
            @click="emit('selectFlight', flight)"
          >
            <td colspan="8" class="px-2.5 pt-0 pb-2.5">
              <div v-if="cheapestReturnsLoading" class="text-xs text-[#999] dark:text-slate-500">
                Loading return...
              </div>
              <div v-else-if="getReturn(flight)" class="flex flex-wrap items-center gap-x-3 text-xs text-[#777] dark:text-slate-400">
                <span class="font-semibold text-[#555] dark:text-slate-300">Return Nov 22</span>
                <span>{{ getReturn(flight)!.airlineName }}</span>
                <span>{{ formatTime(getReturn(flight)!.departure) }}&ndash;{{ formatTime(getReturn(flight)!.arrival) }}</span>
                <span>{{ formatDuration(getReturn(flight)!.duration) }}</span>
                <span class="font-semibold">{{ formatPrice(getReturn(flight)!.price) }}</span>
              </div>
              <div v-else class="text-xs text-[#bbb] dark:text-slate-600">
                No direct return available
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
    <p v-if="flights.length === 0" class="p-8 text-center text-[#888] dark:text-slate-500">
      No direct flights found matching your filters.
    </p>
  </div>
</template>
