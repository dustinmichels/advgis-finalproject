<template>
  <div v-if="dataField" class="modal is-active">
    <div class="modal-background" @click="closeModal"></div>
    <div class="modal-card">
      <header class="modal-card-head">
        <p class="modal-card-title">Settings: {{ displayName }}</p>
        <button class="delete" aria-label="close" @click="closeModal"></button>
      </header>
      <section class="modal-card-body">
        <div v-if="parameterData">
          <p class="mb-4">{{ parameterData.notes }}</p>

          <h4 class="title is-6">Categories:</h4>
          <div v-for="(category, key) in parameterData.categories" :key="key" class="box mb-3">
            <div class="is-flex is-justify-content-space-between is-align-items-center mb-2">
              <strong class="is-capitalized">{{ formatCategoryName(key) }}</strong>
              <span class="tag is-info">Score: {{ category.score }}</span>
            </div>
            <p class="is-size-7">{{ category.notes }}</p>
            <img
              v-if="category.img"
              :src="category.img"
              alt=""
              class="mt-2"
              style="max-width: 100%; height: auto"
            />
          </div>

          <a
            v-if="parameterData.link"
            :href="parameterData.link"
            target="_blank"
            class="button is-link is-small mt-4"
          >
            <span class="icon is-small">
              <i class="fas fa-external-link-alt"></i>
            </span>
            <span>Learn More on OpenStreetMap Wiki</span>
          </a>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { BIKE_INFRASTRUCTURE_DATA } from '@/data/bikeData'
import { computed, onMounted, onUnmounted } from 'vue'

interface Props {
  dataField: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
}>()

// Computed property to get the parameter data
const parameterData = computed(() => {
  if (!props.dataField) return null
  return BIKE_INFRASTRUCTURE_DATA[props.dataField as keyof typeof BIKE_INFRASTRUCTURE_DATA]
})

// Computed property for display name
const displayName = computed(() => {
  if (!props.dataField) return ''
  const displayNames: Record<string, string> = {
    separation_level: 'Separation Level',
    speed_limit: 'Speed Limit',
    street_classification: 'Street Classification (Busyness)',
  }
  return displayNames[props.dataField] || props.dataField
})

// Helper function to format category names nicely
const formatCategoryName = (key: string): string => {
  return key.replace(/_/g, ' ').replace(/-/g, ' ')
}

// Close modal
const closeModal = () => {
  emit('close')
}

// Handle Escape key press
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && props.dataField) {
    closeModal()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.modal-card-body .box {
  background-color: #f5f5f5;
}

/* Ensure modal appears above map */
.modal {
  z-index: 99999 !important;
}

.modal-background {
  z-index: 99998 !important;
}

.modal-card {
  z-index: 100000 !important;
}
</style>
