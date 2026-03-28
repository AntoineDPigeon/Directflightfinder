<script setup lang="ts">
import type { FavoriteCombo } from '@/types'

defineProps<{
  favorites: FavoriteCombo[]
  currentPrices: Record<string, { outbound: string; ret: string } | null>
}>()

const emit = defineEmits<{
  remove: [id: string]
}>()

function formatPrice(price: string | number): string {
  const num = typeof price === 'string' ? parseFloat(price) : price
  return new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' }).format(num)
}

function formatTime(isoStr: string): string {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return d.toLocaleTimeString('en-CA', { hour: '2-digit', minute: '2-digit', hour12: false })
}

function formatDate(isoStr: string): string {
  if (!isoStr) return ''
  const d = new Date(isoStr + (isoStr.includes('T') ? '' : 'T12:00:00'))
  return d.toLocaleDateString('en-CA', { weekday: 'short', month: 'short', day: 'numeric' })
}

function formatDuration(iso: string): string {
  if (!iso) return ''
  const match = iso.match(/PT(?:(\d+)H)?(?:(\d+)M)?/)
  if (!match) return iso
  const h = match[1] ? `${match[1]}h` : ''
  const m = match[2] ? ` ${match[2]}m` : ''
  return `${h}${m}`.trim()
}

function savedTotal(fav: FavoriteCombo): number {
  return parseFloat(fav.savedTotal)
}

function currentTotal(fav: FavoriteCombo, prices: Record<string, { outbound: string; ret: string } | null>): number | null {
  const p = prices[fav.id]
  if (!p) return null
  return parseFloat(p.outbound) + parseFloat(p.ret)
}

function priceDiff(fav: FavoriteCombo, prices: Record<string, { outbound: string; ret: string } | null>): number | null {
  const curr = currentTotal(fav, prices)
  if (curr === null) return null
  return curr - savedTotal(fav)
}
</script>

<template>
  <div v-if="favorites.length > 0" class="mb-6 rounded-lg border border-amber-300 bg-amber-50 p-4 dark:border-amber-700 dark:bg-amber-900/20">
    <h2 class="mb-3 text-sm font-bold uppercase tracking-wide text-amber-800 dark:text-amber-400">Saved Combinations</h2>
    <div class="flex flex-col gap-3">
      <div
        v-for="fav in favorites"
        :key="fav.id"
        class="rounded-lg border border-amber-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800"
      >
        <div class="flex flex-wrap items-start justify-between gap-3">
          <!-- Flight info -->
          <div class="flex-1 min-w-0">
            <div class="mb-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
              <span class="font-bold text-[#1a3a5c] dark:text-blue-300">{{ fav.outbound.origin }} &harr; FLL</span>
              <span class="text-xs text-[#777] dark:text-slate-400">Round trip</span>
            </div>
            <div class="grid gap-1 text-xs text-[#555] dark:text-slate-400 sm:grid-cols-2">
              <div>
                <span class="font-semibold">Out:</span>
                {{ formatDate(fav.outbound.departure) }} &middot;
                {{ fav.outbound.airline }} &middot;
                {{ formatTime(fav.outbound.departure) }}&ndash;{{ formatTime(fav.outbound.arrival) }} &middot;
                {{ formatDuration(fav.outbound.duration) }}
              </div>
              <div>
                <span class="font-semibold">Ret:</span>
                {{ formatDate(fav.returnDate) }} &middot;
                {{ fav.returnFlight.airline }} &middot;
                {{ formatTime(fav.returnFlight.departure) }}&ndash;{{ formatTime(fav.returnFlight.arrival) }} &middot;
                {{ formatDuration(fav.returnFlight.duration) }}
              </div>
            </div>
          </div>

          <!-- Price info -->
          <div class="flex items-center gap-4 text-right">
            <div>
              <div class="text-xs text-[#888] dark:text-slate-500">Saved at</div>
              <div class="font-bold text-[#1a3a5c] dark:text-blue-300">{{ formatPrice(savedTotal(fav)) }}</div>
            </div>
            <div v-if="currentPrices[fav.id]">
              <div class="text-xs text-[#888] dark:text-slate-500">Now</div>
              <div class="font-bold" :class="priceDiff(fav, currentPrices)! > 0 ? 'text-red-600 dark:text-red-400' : priceDiff(fav, currentPrices)! < 0 ? 'text-green-600 dark:text-green-400' : 'text-[#1a3a5c] dark:text-blue-300'">
                {{ formatPrice(currentTotal(fav, currentPrices)!) }}
                <span v-if="priceDiff(fav, currentPrices)! !== 0" class="text-xs font-normal">
                  ({{ priceDiff(fav, currentPrices)! > 0 ? '+' : '' }}{{ formatPrice(priceDiff(fav, currentPrices)!) }})
                </span>
              </div>
            </div>
            <div v-else>
              <div class="text-xs text-[#888] dark:text-slate-500">Now</div>
              <div class="text-xs text-[#999] dark:text-slate-500">Loading...</div>
            </div>
            <button
              @click="emit('remove', fav.id)"
              class="cursor-pointer rounded border-none bg-red-100 px-2 py-1 text-xs text-red-700 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50"
              title="Remove"
            >&times;</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
