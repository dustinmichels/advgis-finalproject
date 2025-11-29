<template>
  <div class="box map-component">
    <div class="notification is-danger is-light" v-if="error">
      {{ error }}
    </div>

    <div class="notification is-info is-light" v-if="loading">Loading map data...</div>

    <div ref="mapContainer" class="map-container"></div>

    <!-- Legend -->
    <div class="legend">
      <div class="legend-title">Composite Score</div>
      <div class="legend-gradient" :style="legendGradientStyle"></div>

      <div class="legend-labels">
        <span v-for="n in 11" :key="n - 1">{{ n - 1 }}</span>
      </div>
    </div>

    <!-- Boundary Toggle -->
    <div class="boundary-toggle">
      <label class="checkbox">
        <input type="checkbox" v-model="showBoundary" @change="toggleBoundary" />
        Show Boundary
      </label>
    </div>

    <!-- Color Scale Toggle -->
    <div class="color-toggle">
      <label class="checkbox">
        <input type="checkbox" v-model="useGoodColors" @change="updateColors" />
        Use Good Colors
      </label>
    </div>

    <!-- Score Controls -->
    <div class="score-controls" v-if="showControls">
      <div class="score-control-title">Adjust Weights</div>

      <div class="weight-slider">
        <label>Max Speed Score: {{ weights.maxspeed_int_score.toFixed(1) }}</label>
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          v-model.number="weights.maxspeed_int_score"
          @input="onWeightsChange"
        />
      </div>

      <div class="weight-slider">
        <label>Separation Level Score: {{ weights.separation_level_score.toFixed(1) }}</label>
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          v-model.number="weights.separation_level_score"
          @input="onWeightsChange"
        />
      </div>

      <div class="weight-slider">
        <label
          >Street Classification Score: {{ weights.street_classification_score.toFixed(1) }}</label
        >
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          v-model.number="weights.street_classification_score"
          @input="onWeightsChange"
        />
      </div>

      <div class="weight-slider">
        <label>Lanes Score: {{ weights.lanes_int_score.toFixed(1) }}</label>
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          v-model.number="weights.lanes_int_score"
          @input="onWeightsChange"
        />
      </div>

      <button class="button is-small" @click="resetWeights">Reset Weights</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  type GeoJsonData,
  type ScoreWeights,
  defaultWeights,
  recalculateAllScores,
} from '@/utils/scoreManager'

import { badColors, goodColors } from '@/utils/colorScale'

import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'

// Fix Leaflet marker assets
import iconRetina from 'leaflet/dist/images/marker-icon-2x.png'
import icon from 'leaflet/dist/images/marker-icon.png'
import iconShadow from 'leaflet/dist/images/marker-shadow.png'

const DefaultIcon = L.icon({
  iconUrl: icon,
  iconRetinaUrl: iconRetina,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})
L.Marker.prototype.options.icon = DefaultIcon

// Props
interface Props {
  showControls?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  showControls: false,
})

// Refs
const mapContainer = ref<HTMLElement | null>(null)
const error = ref('')
const loading = ref(true)
const currentZoom = ref(15)
const currentLineWidth = ref(3)
const showBoundary = ref(true)
const useGoodColors = ref(true)

// GeoJSON data
const originalGeoJson = ref<GeoJsonData | null>(null)
const currentGeoJson = ref<GeoJsonData | null>(null)
const boundaryGeoJson = ref<any | null>(null)

// Score weights
const weights = reactive<ScoreWeights>({ ...defaultWeights })

// Leaflet layers
let map: L.Map | null = null
let geojsonLayer: L.GeoJSON | null = null
let boundaryLayer: L.GeoJSON | null = null

/* ------------------------------------------------------------
  COLOR SCALE ACCESS
------------------------------------------------------------ */

const getColorForScore = (score: number): string => {
  const colors = useGoodColors.value ? goodColors : badColors
  const clamped = Math.max(0, Math.min(10, score))
  return colors[Math.round(clamped)]
}

// Legend gradient style computed from color scale
const legendGradientStyle = computed(() => {
  const colors = useGoodColors.value ? goodColors : badColors
  const stops = colors.map((c, i) => `${c} ${(i / (colors.length - 1)) * 100}%`).join(', ')
  return { background: `linear-gradient(to right, ${stops})` }
})

const updateColors = () => {
  if (!geojsonLayer) return
  geojsonLayer.setStyle((feature) => {
    const score = feature?.properties?.composite_score ?? 5
    const zoom = map?.getZoom() ?? 15
    return {
      color: getColorForScore(score),
      weight: getLineWeight(zoom),
      opacity: 0.9,
    }
  })
}

/* ------------------------------------------------------------
  LINE WIDTH VS ZOOM
------------------------------------------------------------ */
const getLineWeight = (zoom: number): number => {
  if (zoom <= 12) return 1
  if (zoom <= 14) return 2
  if (zoom <= 16) return 3
  if (zoom <= 18) return 5
  return 7
}

/* ------------------------------------------------------------
  MAP INIT
------------------------------------------------------------ */
onMounted(async () => {
  if (mapContainer.value) {
    map = L.map(mapContainer.value).setView([42.3876, -71.0995], 15)

    L.tileLayer('https://tiles.stadiamaps.com/tiles/stamen_toner_dark/{z}/{x}/{y}{r}.png', {
      minZoom: 0,
      maxZoom: 20,
      attribution:
        '&copy; <a href="https://www.stadiamaps.com/">Stadia Maps</a> ' +
        '&copy; <a href="https://www.stamen.com/">Stamen Design</a> ' +
        '&copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> ' +
        '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
    }).addTo(map)

    map.on('zoomend', () => {
      if (geojsonLayer && map) {
        const zoom = map.getZoom()
        const lineWeight = getLineWeight(zoom)

        currentZoom.value = zoom
        currentLineWidth.value = lineWeight

        geojsonLayer.setStyle((feature) => {
          const score = feature?.properties?.composite_score ?? 5
          return {
            color: getColorForScore(score),
            weight: lineWeight,
            opacity: 0.9,
          }
        })
      }
    })

    await loadBoundary()
    await loadGeoJson()
  }
})

onUnmounted(() => {
  map?.remove()
  map = null
})

/* ------------------------------------------------------------
  BOUNDARY
------------------------------------------------------------ */
const loadBoundary = async () => {
  try {
    const response = await fetch('/somerville_boundary.geojson')
    if (!response.ok) return

    const data = await response.json()
    boundaryGeoJson.value = data
    addBoundaryToMap(data)
  } catch {}
}

const addBoundaryToMap = (geojsonData: any) => {
  if (!map) return

  if (boundaryLayer) map.removeLayer(boundaryLayer)

  boundaryLayer = L.geoJSON(geojsonData, {
    style: {
      fillColor: '#001a33',
      fillOpacity: 0.08,
      color: '#ff1493',
      weight: 4,
      opacity: 0.7,
      dashArray: '4 6',
    },
  }).addTo(map)
}

/* ------------------------------------------------------------
  GEOJSON LOADING
------------------------------------------------------------ */
const loadGeoJson = async () => {
  try {
    loading.value = true
    error.value = ''

    const response = await fetch('/somerville_streets.geojson')
    if (!response.ok) throw new Error(`HTTP error: ${response.status}`)

    const data = await response.json()
    originalGeoJson.value = data
    currentGeoJson.value = recalculateAllScores(data, weights)

    addGeoJsonToMap(currentGeoJson.value)

    if (map) {
      currentZoom.value = map.getZoom()
      currentLineWidth.value = getLineWeight(currentZoom.value)
    }
  } catch (e) {
    error.value = `Error loading GeoJSON: ${e instanceof Error ? e.message : 'Unknown error'}`
  } finally {
    loading.value = false
  }
}

const addGeoJsonToMap = (geojsonData: GeoJsonData) => {
  if (!map) return

  if (geojsonLayer) map.removeLayer(geojsonLayer)

  geojsonLayer = L.geoJSON(geojsonData, {
    onEachFeature: (feature, layer) => {
      if (feature.properties) {
        const popup = Object.entries(feature.properties)
          .map(([k, v]) => `<strong>${k}:</strong> ${typeof v === 'number' ? v.toFixed(2) : v}`)
          .join('<br>')
        layer.bindPopup(popup)
      }
    },
    style: (feature) => {
      const score = feature?.properties?.composite_score ?? 5
      const zoom = map?.getZoom() ?? 15

      return {
        color: getColorForScore(score),
        weight: getLineWeight(zoom),
        opacity: 0.9,
      }
    },
  }).addTo(map)

  const bounds = geojsonLayer.getBounds()
  if (bounds.isValid()) map.fitBounds(bounds, { padding: [50, 50] })
}

/* ------------------------------------------------------------
  SCORE WEIGHTS
------------------------------------------------------------ */
const onWeightsChange = () => {
  if (!originalGeoJson.value) return
  currentGeoJson.value = recalculateAllScores(originalGeoJson.value, weights)
  addGeoJsonToMap(currentGeoJson.value)
}

const resetWeights = () => {
  Object.assign(weights, defaultWeights)
  onWeightsChange()
}

/* ------------------------------------------------------------
  BOUNDARY TOGGLE
------------------------------------------------------------ */
const toggleBoundary = () => {
  if (!map || !boundaryLayer) return
  showBoundary.value ? map.addLayer(boundaryLayer) : map.removeLayer(boundaryLayer)
}

/* ------------------------------------------------------------
  EXPOSE
------------------------------------------------------------ */
defineExpose({
  recalculateScores: onWeightsChange,
  resetScores: resetWeights,
  setWeights: (w: Partial<ScoreWeights>) => {
    Object.assign(weights, w)
    onWeightsChange()
  },
})
</script>

<style scoped>
.map-component {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  position: relative;
}

.map-container {
  flex: 1;
  min-height: 400px;
  border-radius: 4px;
  overflow: hidden;
}

/* Legend */
.legend {
  position: absolute;
  bottom: 20px;
  left: 20px;
  background: white;
  padding: 10px 15px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}

.legend-title {
  font-weight: bold;
  margin-bottom: 8px;
  font-size: 14px;
}

.legend-gradient {
  width: 220px;
  height: 20px;
  border-radius: 2px;
  margin-bottom: 5px;
}

.legend-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #666;
}

.legend-labels span {
  width: 20px;
  text-align: center;
}

/* Boundary toggle */
.boundary-toggle {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: white;
  padding: 10px 15px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}

.boundary-toggle .checkbox {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* Color toggle */
.color-toggle {
  position: absolute;
  bottom: 80px;
  right: 20px;
  background: white;
  padding: 10px 15px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}

.color-toggle .checkbox {
  display: flex;
  gap: 8px;
  align-items: center;
}

/* Score controls */
.score-controls {
  position: absolute;
  top: 80px;
  right: 20px;
  background: white;
  padding: 15px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  min-width: 250px;
}

.score-control-title {
  font-weight: bold;
  margin-bottom: 12px;
}

.weight-slider {
  margin-bottom: 12px;
}

.weight-slider label {
  display: block;
  font-size: 13px;
  margin-bottom: 4px;
}

.weight-slider input[type='range'] {
  width: 100%;
}

.button {
  width: 100%;
  margin-top: 8px;
}
</style>
