import type { BikeInfrastructureModel, ModelWeights, StreetProperties } from '@/types'

/**
 * Calculate the separation level score for a street
 * Uses the 'separation_level' field from GeoJSON (e.g., "lane", "track", "none")
 */
export const calculateSeparationScore = (
  properties: StreetProperties,
  modelConfig: BikeInfrastructureModel,
): number => {
  const category = properties.separation_level

  if (!category) {
    const defaultCat = modelConfig.separation_level.defaultCategory || 'none'
    const score = modelConfig.separation_level.categories[String(defaultCat)]?.score ?? 5
    return score
  }

  const score = modelConfig.separation_level.categories[category]?.score

  if (score === undefined) {
    console.warn(`Unknown separation_level category '${category}', using default`)
    const defaultCat = modelConfig.separation_level.defaultCategory || 'none'
    return modelConfig.separation_level.categories[String(defaultCat)]?.score ?? 5
  }

  return score
}

/**
 * Calculate the street classification score for a street
 * Uses the 'street_classification' field from GeoJSON (e.g., "residential", "medium-capacity")
 */
export const calculateStreetClassificationScore = (
  properties: StreetProperties,
  modelConfig: BikeInfrastructureModel,
): number => {
  const category = properties.street_classification

  if (!category) {
    const defaultCat = modelConfig.street_classification.defaultCategory || 'residential'
    const score = modelConfig.street_classification.categories[String(defaultCat)]?.score ?? 2
    return score
  }

  const score = modelConfig.street_classification.categories[category]?.score

  if (score === undefined) {
    console.warn(`Unknown street_classification category '${category}', using default`)
    const defaultCat = modelConfig.street_classification.defaultCategory || 'residential'
    return modelConfig.street_classification.categories[String(defaultCat)]?.score ?? 2
  }

  return score
}

/**
 * Calculate the speed limit score for a street
 * Uses the 'maxspeed_int' field from GeoJSON (integer value like 25, 30, 40)
 */
export const calculateSpeedScore = (
  properties: StreetProperties,
  modelConfig: BikeInfrastructureModel,
): number => {
  const maxspeedValue = properties.maxspeed_int

  // Helper function to map speed to category
  const speedToCategory = (speed: number): string => {
    if (speed <= 20) return '20_mph_or_less'
    if (speed <= 25) return '25_mph'
    if (speed <= 30) return '30_mph'
    if (speed <= 40) return '40_mph'
    if (speed <= 50) return '50_mph'
    return 'over_50_mph'
  }

  if (maxspeedValue === undefined || maxspeedValue === null) {
    const defaultSpeed = Number(modelConfig.speed_limit.defaultCategory) || 25
    const category = speedToCategory(defaultSpeed)
    return modelConfig.speed_limit.categories[category]?.score ?? 1
  }

  // Convert to number if it's a string
  const speed = typeof maxspeedValue === 'number' ? maxspeedValue : parseInt(String(maxspeedValue))

  if (isNaN(speed)) {
    console.warn(`Invalid maxspeed_int value '${maxspeedValue}', using default`)
    const defaultSpeed = Number(modelConfig.speed_limit.defaultCategory) || 25
    const category = speedToCategory(defaultSpeed)
    return modelConfig.speed_limit.categories[category]?.score ?? 1
  }

  const category = speedToCategory(speed)
  const score = modelConfig.speed_limit.categories[category]?.score

  if (score === undefined) {
    console.warn(`Unknown speed category '${category}', using default`)
    const defaultSpeed = Number(modelConfig.speed_limit.defaultCategory) || 25
    const defaultCategory = speedToCategory(defaultSpeed)
    return modelConfig.speed_limit.categories[defaultCategory]?.score ?? 1
  }

  return score
}

/**
 * Calculate the composite score using weighted average
 */
export const calculateCompositeScore = (
  separationScore: number,
  streetClassScore: number,
  speedScore: number,
  weights: ModelWeights,
): number => {
  // Convert percentage weights to proportions
  const total = weights.separation_level + weights.speed + weights.busyness

  if (total === 0) return 0

  const normalizedWeights = {
    separation: weights.separation_level / total,
    speed: weights.speed / total,
    busyness: weights.busyness / total,
  }

  return (
    separationScore * normalizedWeights.separation +
    speedScore * normalizedWeights.speed +
    streetClassScore * normalizedWeights.busyness
  )
}

/**
 * Calculate all scores for a single street feature
 */
let calculationCount = 0

export const calculateAllScores = (
  properties: StreetProperties,
  modelConfig: BikeInfrastructureModel,
  weights: ModelWeights,
): {
  separation_level_score: number
  street_classification_score: number
  maxspeed_int_score: number
  composite_score: number
} => {
  const separationScore = calculateSeparationScore(properties, modelConfig)
  const streetClassScore = calculateStreetClassificationScore(properties, modelConfig)
  const speedScore = calculateSpeedScore(properties, modelConfig)
  const compositeScore = calculateCompositeScore(
    separationScore,
    streetClassScore,
    speedScore,
    weights,
  )

  // Debug logging for the first 5 features
  if (calculationCount < 5) {
    console.log(`Calculation ${calculationCount + 1}:`, {
      input: {
        separation_level: properties.separation_level,
        street_classification: properties.street_classification,
        maxspeed_int: properties.maxspeed_int,
      },
      intermediateScores: {
        separation: separationScore,
        streetClass: streetClassScore,
        speed: speedScore,
      },
      weights,
      finalComposite: compositeScore,
    })
    calculationCount++
  }

  return {
    separation_level_score: separationScore,
    street_classification_score: streetClassScore,
    maxspeed_int_score: speedScore,
    composite_score: compositeScore,
  }
}
