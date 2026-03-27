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
  { value: 'price', label: 'Price (lowest first)' },
  { value: 'departure', label: 'Departure time' },
  { value: 'origin', label: 'Airport' },
  { value: 'airline', label: 'Airline' },
]
</script>

<template>
  <div class="filters">
    <div class="filter-group">
      <div class="filter-header">
        <h3>Departure Airports</h3>
        <span class="filter-actions">
          <button @click="emit('selectAllAirports')" class="link-btn">All</button>
          <button @click="emit('clearAllAirports')" class="link-btn">None</button>
        </span>
      </div>
      <div class="checkbox-grid">
        <label
          v-for="airport in airports"
          :key="airport.code"
          class="checkbox-item"
        >
          <input
            type="checkbox"
            :checked="selectedAirports.has(airport.code)"
            @change="emit('toggleAirport', airport.code)"
          />
          <span class="airport-label">
            <strong>{{ airport.code }}</strong>
            <span class="airport-detail">{{ airport.name }} ({{ airport.drive }})</span>
          </span>
        </label>
      </div>
    </div>

    <div class="filter-group">
      <div class="filter-header">
        <h3>Dates</h3>
        <span class="filter-actions">
          <button @click="emit('selectAllDates')" class="link-btn">All</button>
          <button @click="emit('clearAllDates')" class="link-btn">None</button>
        </span>
      </div>
      <div class="checkbox-row">
        <label
          v-for="date in dates"
          :key="date"
          class="checkbox-item"
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

    <div class="filter-group sort-group">
      <h3>Sort by</h3>
      <select :value="sortField" @change="emit('updateSort', ($event.target as HTMLSelectElement).value as SortField)">
        <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </div>
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding: 1.25rem;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.filter-group h3 {
  margin: 0 0 0.5rem;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #555;
}

.filter-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.filter-actions {
  display: flex;
  gap: 0.5rem;
}

.link-btn {
  background: none;
  border: none;
  color: #0066cc;
  cursor: pointer;
  font-size: 0.8rem;
  padding: 0;
  text-decoration: underline;
}

.link-btn:hover {
  color: #004499;
}

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 0.35rem;
}

.checkbox-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
  font-size: 0.9rem;
}

.airport-label {
  display: flex;
  align-items: baseline;
  gap: 0.35rem;
}

.airport-detail {
  font-size: 0.8rem;
  color: #666;
}

.sort-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.sort-group h3 {
  margin: 0;
}

select {
  padding: 0.4rem 0.6rem;
  border-radius: 4px;
  border: 1px solid #ccc;
  font-size: 0.9rem;
}
</style>
