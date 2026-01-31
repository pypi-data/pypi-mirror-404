/**
 * Generic particle system for managing particle effects
 */

import { Particle } from "./types"

export class ParticleSystem {
  particles: Particle[]
  ctx: CanvasRenderingContext2D

  constructor(ctx: CanvasRenderingContext2D) {
    this.ctx = ctx
    this.particles = []
  }

  addParticle(particle: Particle): void {
    this.particles.push(particle)
  }

  update(): void {
    this.particles = this.particles.filter((particle) => {
      // Update position
      particle.x += particle.vx
      particle.y += particle.vy

      // Update rotation if applicable
      if (particle.rotation !== undefined && particle.rotationSpeed !== undefined) {
        particle.rotation += particle.rotationSpeed
      }

      // Fade out based on opacity
      if (particle.opacity !== undefined) {
        particle.opacity -= 0.005
      }

      // Remove particles that are off screen or faded out
      return (
        particle.opacity > 0 &&
        particle.x > -100 &&
        particle.x < window.innerWidth + 100 &&
        particle.y < window.innerHeight + 100
      )
    })
  }

  draw(): void {
    this.particles.forEach((particle) => {
      this.ctx.save()
      this.ctx.globalAlpha = particle.opacity || 1
      this.ctx.fillStyle = particle.color

      if (particle.rotation !== undefined) {
        this.ctx.translate(particle.x, particle.y)
        this.ctx.rotate(particle.rotation)
        this.ctx.fillRect(-particle.size / 2, -particle.size / 2, particle.size, particle.size)
      } else {
        this.ctx.beginPath()
        this.ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2)
        this.ctx.fill()
      }

      this.ctx.restore()
    })
  }

  clear(): void {
    this.particles = []
  }

  count(): number {
    return this.particles.length
  }
}
