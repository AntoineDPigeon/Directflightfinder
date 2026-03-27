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
  <div class="table-wrapper">
    <table>
      <thead>
        <tr>
          <th>Origin</th>
          <th>Date</th>
          <th>Airline</th>
          <th>Flight</th>
          <th>Departure</th>
          <th>Arrival</th>
          <th>Duration</th>
          <th class="price-col">Price (CAD)</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(flight, i) in flights"
          :key="i"
          :class="{ cheapest: isCheapest(flight, cheapestByAirport) }"
        >
          <td>
            <strong>{{ flight.origin }}</strong>
            <span class="origin-name">{{ flight.originName }}</span>
          </td>
          <td>{{ formatDate(flight.departure) }}</td>
          <td>{{ flight.airlineName }}</td>
          <td>{{ flight.flightNumber }}</td>
          <td>{{ formatTime(flight.departure) }}</td>
          <td>{{ formatTime(flight.arrival) }}</td>
          <td>{{ formatDuration(flight.duration) }}</td>
          <td class="price-col">{{ formatPrice(flight.price) }}</td>
        </tr>
      </tbody>
    </table>
    <p v-if="flights.length === 0" class="no-results">
      No direct flights found matching your filters.
    </p>
  </div>
</template>

<style scoped>
.table-wrapper {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

thead {
  background: #1a3a5c;
  color: #fff;
}

th {
  padding: 0.75rem 0.6rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

td {
  padding: 0.6rem;
  border-bottom: 1px solid #e8e8e8;
}

tbody tr:nth-child(even) {
  background: #f9fafb;
}

tbody tr:hover {
  background: #eef3f8;
}

tr.cheapest {
  background: #e8f5e9 !important;
}

tr.cheapest td {
  font-weight: 500;
}

.price-col {
  text-align: right;
  font-weight: 700;
  white-space: nowrap;
}

.origin-name {
  display: block;
  font-size: 0.75rem;
  color: #777;
}

.no-results {
  text-align: center;
  padding: 2rem;
  color: #888;
  font-size: 1rem;
}
</style>
