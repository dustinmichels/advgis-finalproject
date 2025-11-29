// Type definitions for the bike infrastructure scoring system

export interface CategoryData {
  score: number
  displayLabel: string
  img?: string
  notes: string
}

export interface ParameterData {
  weight: number
  displayLabel: string
  img?: string
  link?: string
  notes: string
  categories: Record<string, CategoryData>
}

export interface BikeInfrastructureModel {
  separation_level: ParameterData
  street_classification: ParameterData
  speed_limit: ParameterData
}

export interface ModelWeights {
  separation_level: number
  speed: number
  busyness: number
}

export interface StreetProperties {
  // Category fields from GeoJSON (these are the actual values we use for scoring)
  separation_level?: string // e.g., "lane", "track", "none"
  street_classification?: string // e.g., "residential", "medium-capacity"
  maxspeed_int?: string // e.g., "25_mph", "30_mph"

  // Other properties
  name?: string

  // Computed scores (will be calculated dynamically)
  separation_level_score?: number
  street_classification_score?: number
  maxspeed_int_score?: number
  composite_score?: number

  [key: string]: any
}

export interface GeoJsonFeature {
  type: string
  properties: StreetProperties
  geometry: any
}

export interface GeoJsonData {
  type: string
  features: GeoJsonFeature[]
}
