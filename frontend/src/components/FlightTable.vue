<script setup lang="ts">
import type { Flight } from '@/types'

defineProps<{
  flights: Flight[]
  cheapestByAirport: Record<string, number>
}>()

function formatPrice(price: string): string {
  const num = parseFloat(price)
  return new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' }).format(num)
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
</script>

<template>
  <div class="overflow-x-auto">
    <table class="w-full border-collapse text-sm">
      <thead class="bg-[#1a3a5c] text-white">
        <tr>
          <th class="px-2.5 py-3 text-left text-xs font-semibold uppercase tracking-wide">Origin</th>
          <th class="px-2.5 py-3 text-left text-xs font-semibold uppercase tracking-wide">Date</th>
          <th class="px-2.5 py-3 text-left text-xs font-semibold uppercase tracking-wide">Airline</th>
          <th class="px-2.5 py-3 text-left text-xs font-semibold uppercase tracking-wide">Flight</th>
          <th class="px-2.5 py-3 text-left text-xs font-semibold uppercase tracking-wide">Departure</th>
          <th class="px-2.5 py-3 text-left text-xs font-semibold uppercase tracking-wide">Arrival</th>
          <th class="px-2.5 py-3 text-left text-xs font-semibold uppercase tracking-wide">Duration</th>
          <th class="px-2.5 py-3 text-right text-xs font-bold uppercase tracking-wide whitespace-nowrap">Price (CAD)</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(flight, i) in flights"
          :key="i"
          class="border-b border-[#e8e8e8] even:bg-[#f9fafb] hover:bg-[#eef3f8]"
          :class="{ '!bg-[#e8f5e9] font-medium': isCheapest(flight, cheapestByAirport) }"
        >
          <td class="px-2.5 py-2.5">
            <strong>{{ flight.origin }}</strong>
            <span class="block text-xs text-[#777]">{{ flight.originName }}</span>
          </td>
          <td class="px-2.5 py-2.5">{{ formatDate(flight.departure) }}</td>
          <td class="px-2.5 py-2.5">{{ flight.airlineName }}</td>
          <td class="px-2.5 py-2.5">{{ flight.flightNumber }}</td>
          <td class="px-2.5 py-2.5">{{ formatTime(flight.departure) }}</td>
          <td class="px-2.5 py-2.5">{{ formatTime(flight.arrival) }}</td>
          <td class="px-2.5 py-2.5">{{ formatDuration(flight.duration) }}</td>
          <td class="px-2.5 py-2.5 text-right font-bold whitespace-nowrap">{{ formatPrice(flight.price) }}</td>
        </tr>
      </tbody>
    </table>
    <p v-if="flights.length === 0" class="p-8 text-center text-[#888]">
      No direct flights found matching your filters.
    </p>
  </div>
</template>
