<script setup lang="ts">
import { computed } from 'vue'
import type { Airport, SortField } from '@/types'

const props = defineProps<{
  airports: Airport[]
  dates: string[]
  selectedAirports: Set<string>
  selectedDates: Set<string>
  sortField: SortField
}>()

const emit = defineEmits<{
  toggleAirport: [code: string]
  toggleDate: [date: string]
  updateSort: [field: SortField]
  selectAllAirports: []
  clearAllAirports: []
  selectAllDates: []
  clearAllDates: []
}>()

function formatDateLabel(dateStr: string): string {
  const d = new Date(dateStr + 'T12:00:00')
  return d.toLocaleDateString('en-CA', { weekday: 'short', month: 'short', day: 'numeric' })
}

const sortOptions: { value: SortField; label: string }[] = [
  { value: 'price', label: 'Outbound price (lowest first)' },
  { value: 'roundTrip', label: 'Round trip price (lowest first)' },
  { value: 'departure', label: 'Departure time' },
  { value: 'origin', label: 'Airport' },
  { value: 'airline', label: 'Airline' },
]
</script>

<template>
  <div class="flex flex-col gap-5 rounded-lg border border-[#e0e0e0] bg-[#f8f9fa] p-5 dark:border-slate-700 dark:bg-slate-800">
    <div>
      <div class="flex items-center gap-3">
        <h3 class="mb-2 text-sm uppercase tracking-wide text-[#555] dark:text-slate-400">Departure Airports</h3>
        <span class="flex gap-2">
          <button @click="emit('selectAllAirports')" class="cursor-pointer border-none bg-transparent p-0 text-xs text-[#0066cc] underline hover:text-[#004499] dark:text-blue-400 dark:hover:text-blue-300">All</button>
          <button @click="emit('clearAllAirports')" class="cursor-pointer border-none bg-transparent p-0 text-xs text-[#0066cc] underline hover:text-[#004499] dark:text-blue-400 dark:hover:text-blue-300">None</button>
        </span>
      </div>
      <div class="grid grid-cols-[repeat(auto-fill,minmax(260px,1fr))] gap-1">
        <label
          v-for="airport in airports"
          :key="airport.code"
          class="flex cursor-pointer items-center gap-1.5 text-sm"
        >
          <input
            type="checkbox"
            :checked="selectedAirports.has(airport.code)"
            @change="emit('toggleAirport', airport.code)"
          />
          <span class="flex items-baseline gap-1">
            <strong>{{ airport.code }}</strong>
            <span class="text-xs text-[#666] dark:text-slate-400">{{ airport.name }} ({{ airport.drive }})</span>
          </span>
        </label>
      </div>
    </div>

    <div>
      <div class="flex items-center gap-3">
        <h3 class="mb-2 text-sm uppercase tracking-wide text-[#555] dark:text-slate-400">Dates</h3>
        <span class="flex gap-2">
          <button @click="emit('selectAllDates')" class="cursor-pointer border-none bg-transparent p-0 text-xs text-[#0066cc] underline hover:text-[#004499] dark:text-blue-400 dark:hover:text-blue-300">All</button>
          <button @click="emit('clearAllDates')" class="cursor-pointer border-none bg-transparent p-0 text-xs text-[#0066cc] underline hover:text-[#004499] dark:text-blue-400 dark:hover:text-blue-300">None</button>
        </span>
      </div>
      <div class="flex flex-wrap gap-3">
        <label
          v-for="date in dates"
          :key="date"
          class="flex cursor-pointer items-center gap-1.5 text-sm"
        >
          <input
            type="checkbox"
            :checked="selectedDates.has(date)"
            @change="emit('toggleDate', date)"
          />
          {{ formatDateLabel(date) }}
        </label>
      </div>
    </div>

    <div class="flex items-center gap-3">
      <h3 class="text-sm uppercase tracking-wide text-[#555] dark:text-slate-400">Sort by</h3>
      <select
        :value="sortField"
        @change="emit('updateSort', ($event.target as HTMLSelectElement).value as SortField)"
        class="rounded border border-[#ccc] bg-white px-2.5 py-1.5 text-sm dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200"
      >
        <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </div>
  </div>
</template>
