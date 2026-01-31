/**
 * Type definitions for streamlit-effects components
 */

export interface BaseEffectProps {
  z_index: number
  duration?: number
}

export interface SnowEffectProps extends BaseEffectProps {
  intensity: string
  speed: number
  color: string
  particle_count: number
}

export interface ConfettiEffectProps extends BaseEffectProps {
  particle_count: number
  colors: string[]
  spread: number
  origin_x: number
  origin_y: number
  velocity: number
}

export interface FireworksEffectProps extends BaseEffectProps {
  intensity: string
  colors: string[]
  launch_count: number
  particles_per_explosion: number
}

export interface HeartsEffectProps extends BaseEffectProps {
  intensity: string
  speed: number
  colors: string[]
  particle_count: number
}

export interface MatrixEffectProps extends BaseEffectProps {
  intensity: string
  speed: number
  color: string
  font_size: number
  column_density: number
}

export interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  size: number
  color: string
  opacity: number
  rotation?: number
  rotationSpeed?: number
}
