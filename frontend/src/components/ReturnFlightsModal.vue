<script setup lang="ts">
import type { ReturnFlight } from '@/types'

defineProps<{
  flights: ReturnFlight[]
  destination: string
  destinationName: string
  date: string
  loading: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

function formatPrice(price: string, currency: string = 'CAD'): string {
  const num = parseFloat(price)
  return new Intl.NumberFormat('en-CA', { style: 'currency', currency }).format(num)
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
  return d.toLocaleDateString('en-CA', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="emit('close')">
    <div class="mx-4 max-h-[80vh] w-full max-w-3xl overflow-hidden rounded-xl bg-white shadow-2xl">
      <div class="flex items-center justify-between border-b border-gray-200 bg-[#1a3a5c] px-6 py-4 text-white">
        <div>
          <h2 class="text-lg font-bold">Return Flights: FLL &rarr; {{ destination }}</h2>
          <p class="text-sm text-blue-200">{{ destinationName }} &middot; {{ formatDateLabel(date) }}</p>
        </div>
        <button
          @click="emit('close')"
          class="flex size-8 cursor-pointer items-center justify-center rounded-full border-none bg-white/20 text-lg text-white hover:bg-white/30"
        >
          &times;
        </button>
      </div>

      <div class="overflow-y-auto p-6" style="max-height: calc(80vh - 72px)">
        <div v-if="loading" class="flex flex-col items-center gap-4 py-12 text-[#555]">
          <div class="size-10 animate-spin rounded-full border-4 border-[#e0e0e0] border-t-[#1a3a5c]"></div>
          Searching for return flights...
        </div>

        <div v-else-if="flights.length === 0" class="py-12 text-center text-[#888]">
          No direct return flights found for this route.
        </div>

        <table v-else class="w-full border-collapse text-sm">
          <thead class="bg-gray-100">
            <tr>
              <th class="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-[#555]">Airline</th>
              <th class="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-[#555]">Flight</th>
              <th class="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-[#555]">Departure</th>
              <th class="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-[#555]">Arrival</th>
              <th class="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-[#555]">Duration</th>
              <th class="px-3 py-2.5 text-right text-xs font-bold uppercase tracking-wide text-[#555]">Price (CAD)</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(flight, i) in flights"
              :key="i"
              class="border-b border-gray-200 even:bg-gray-50 hover:bg-blue-50"
              :class="{ '!bg-[#e8f5e9] font-medium': i === 0 }"
            >
              <td class="px-3 py-2.5">{{ flight.airlineName }}</td>
              <td class="px-3 py-2.5">{{ flight.flightNumber }}</td>
              <td class="px-3 py-2.5">{{ formatTime(flight.departure) }}</td>
              <td class="px-3 py-2.5">{{ formatTime(flight.arrival) }}</td>
              <td class="px-3 py-2.5">{{ formatDuration(flight.duration) }}</td>
              <td class="px-3 py-2.5 text-right font-bold whitespace-nowrap">{{ formatPrice(flight.price, flight.currency) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
