<script setup lang="ts">
import type { Flight, ReturnFlight } from '@/types'

const props = defineProps<{
  flights: ReturnFlight[]
  outboundFlight: Flight
  destination: string
  destinationName: string
  date: string
  loading: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

function formatPrice(price: number): string {
  return new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' }).format(price)
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

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr + 'T12:00:00')
  return d.toLocaleDateString('en-CA', { weekday: 'short', month: 'short', day: 'numeric' })
}

function formatFullDate(dateStr: string): string {
  const d = new Date(dateStr + 'T12:00:00')
  return d.toLocaleDateString('en-CA', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
}

function outboundPrice(): number {
  return parseFloat(props.outboundFlight.price)
}

function combinedPrice(returnFlight: ReturnFlight): number {
  return outboundPrice() + parseFloat(returnFlight.price)
}

function outboundDate(): string {
  return props.outboundFlight.departure.slice(0, 10)
}

function buildRoundTripLink(returnFlight: ReturnFlight): string {
  const origin = props.outboundFlight.origin
  const dest = 'FLL'
  const depDate = outboundDate()
  const retDate = props.date
  return `https://www.google.com/travel/flights?q=Flights%20from%20${origin}%20to%20${dest}%20on%20${depDate}%20return%20${retDate}`
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="emit('close')">
    <div class="mx-4 max-h-[85vh] w-full max-w-4xl overflow-hidden rounded-xl bg-white shadow-2xl dark:bg-slate-900">
      <div class="flex items-center justify-between border-b border-gray-200 bg-[#1a3a5c] px-6 py-4 text-white dark:border-slate-700 dark:bg-slate-950">
        <div>
          <h2 class="text-lg font-bold">Round Trip: {{ outboundFlight.origin }} &harr; FLL</h2>
          <p class="text-sm text-blue-200">{{ destinationName }} &middot; Return {{ formatFullDate(date) }}</p>
        </div>
        <button
          @click="emit('close')"
          class="flex size-8 cursor-pointer items-center justify-center rounded-full border-none bg-white/20 text-lg text-white hover:bg-white/30"
        >
          &times;
        </button>
      </div>

      <div class="overflow-y-auto" style="max-height: calc(85vh - 72px)">
        <!-- Outbound flight summary -->
        <div class="border-b border-gray-200 bg-[#f0f7ff] px-6 py-4 dark:border-slate-700 dark:bg-slate-800">
          <p class="mb-1 text-xs font-semibold uppercase tracking-wide text-[#555] dark:text-slate-400 dark:text-slate-400">Outbound Flight</p>
          <div class="flex flex-wrap items-center gap-x-6 gap-y-1 text-sm">
            <span class="font-bold text-[#1a3a5c] dark:text-blue-300">{{ outboundFlight.origin }} &rarr; FLL</span>
            <span>{{ formatDateLabel(outboundDate()) }}</span>
            <span>{{ outboundFlight.airlineName }}</span>
            <span>{{ formatTime(outboundFlight.departure) }} &ndash; {{ formatTime(outboundFlight.arrival) }}</span>
            <span>{{ formatDuration(outboundFlight.duration) }}</span>
            <span class="font-bold">{{ formatPrice(outboundPrice()) }}</span>
          </div>
        </div>

        <div class="p-6">
          <p class="mb-3 text-xs font-semibold uppercase tracking-wide text-[#555] dark:text-slate-400 dark:text-slate-400">Select a return flight</p>

          <div v-if="loading" class="flex flex-col items-center gap-4 py-12 text-[#555] dark:text-slate-400">
            <div class="size-10 animate-spin rounded-full border-4 border-[#e0e0e0] border-t-[#1a3a5c] dark:border-slate-600 dark:border-t-blue-400"></div>
            Searching for return flights...
          </div>

          <div v-else-if="flights.length === 0" class="py-12 text-center text-[#888] dark:text-slate-500">
            No direct return flights found for this route.
          </div>

          <table v-else class="w-full border-collapse text-sm">
            <thead class="bg-gray-100 dark:bg-slate-800">
              <tr>
                <th class="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-[#555] dark:text-slate-400">Airline</th>
                <th class="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-[#555] dark:text-slate-400">Departure</th>
                <th class="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-[#555] dark:text-slate-400">Arrival</th>
                <th class="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-[#555] dark:text-slate-400">Duration</th>
                <th class="px-3 py-2.5 text-right text-xs font-semibold uppercase tracking-wide text-[#555] dark:text-slate-400">Return</th>
                <th class="px-3 py-2.5 text-right text-xs font-bold uppercase tracking-wide text-[#555] dark:text-slate-400">Total (CAD)</th>
                <th class="px-3 py-2.5 text-center text-xs font-semibold uppercase tracking-wide text-[#555] dark:text-slate-400"></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(flight, i) in flights"
                :key="i"
                class="border-b border-gray-200 even:bg-gray-50 hover:bg-blue-50 dark:border-slate-700 dark:even:bg-slate-800 dark:hover:bg-slate-700"
                :class="{ '!bg-[#e8f5e9] dark:!bg-green-900/40 font-medium': i === 0 }"
              >
                <td class="px-3 py-2.5">{{ flight.airlineName }}</td>
                <td class="px-3 py-2.5">{{ formatTime(flight.departure) }}</td>
                <td class="px-3 py-2.5">{{ formatTime(flight.arrival) }}</td>
                <td class="px-3 py-2.5">{{ formatDuration(flight.duration) }}</td>
                <td class="px-3 py-2.5 text-right text-[#777] dark:text-slate-400">{{ formatPrice(parseFloat(flight.price)) }}</td>
                <td class="px-3 py-2.5 text-right font-bold whitespace-nowrap text-[#1a3a5c] dark:text-blue-300">{{ formatPrice(combinedPrice(flight)) }}</td>
                <td class="px-3 py-2.5 text-center">
                  <a
                    :href="buildRoundTripLink(flight)"
                    target="_blank"
                    rel="noopener"
                    class="inline-block rounded bg-[#0066cc] px-3 py-1 text-xs font-semibold text-white no-underline hover:bg-[#004499] dark:bg-blue-600 dark:hover:bg-blue-500"
                  >Book Both</a>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
