import React, { useEffect, useRef } from "react"
import { FireworksEffectProps } from "../utils/types"
import { ParticleSystem } from "../utils/particleSystem"
import { resizeCanvas, randomRange, randomFromArray, randomInt } from "../utils/canvasHelpers"

const FireworksEffect: React.FC<FireworksEffectProps> = ({
  duration,
  intensity,
  colors,
  launch_count,
  particles_per_explosion,
  z_index,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const particleSystemRef = useRef<ParticleSystem | null>(null)
  const animationRef = useRef<number>()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const handleResize = () => {
      resizeCanvas(canvas)
    }
    handleResize()
    window.addEventListener("resize", handleResize)

    particleSystemRef.current = new ParticleSystem(ctx)

    // Launch firework from bottom to explode at random height
    const launchFirework = () => {
      const displayWidth = canvas.clientWidth
      const displayHeight = canvas.clientHeight
      const startX = randomRange(displayWidth * 0.2, displayWidth * 0.8)
      const explodeX = startX + randomRange(-50, 50)
      const explodeY = randomRange(displayHeight * 0.1, displayHeight * 0.4)
      const color = randomFromArray(colors)
      const launchTime = Date.now()
      const riseTime = randomRange(800, 1200) // ms

      // Create explosion when firework reaches target
      setTimeout(() => {
        createExplosion(explodeX, explodeY, color)
      }, riseTime)
    }

    // Create explosion at target location
    const createExplosion = (x: number, y: number, color: string) => {
      for (let i = 0; i < particles_per_explosion; i++) {
        const angle = randomRange(0, Math.PI * 2)
        const speed = randomRange(1, 8)

        particleSystemRef.current!.addParticle({
          x,
          y,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          size: randomRange(2, 4),
          color,
          opacity: 1.0,
        })
      }
    }

    // Launch fireworks at intervals
    const intervalTime = 1000 / launch_count
    const launchInterval = setInterval(() => {
      if (Date.now() < startTime + duration * 1000) {
        launchFirework()
      }
    }, intervalTime)

    const startTime = Date.now()

    // Animation loop with gravity
    const animate = () => {
      const displayWidth = canvas.clientWidth
      const displayHeight = canvas.clientHeight
      ctx.clearRect(0, 0, displayWidth, displayHeight)

      // Apply gravity and fade
      particleSystemRef.current!.particles.forEach((p) => {
        p.vy += 0.1 // Gravity
        p.opacity -= 0.01 // Fade
      })

      particleSystemRef.current!.update()
      particleSystemRef.current!.draw()

      animationRef.current = requestAnimationFrame(animate)
    }
    animate()

    // Stop after duration
    const timeout = setTimeout(() => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      clearInterval(launchInterval)
    }, duration * 1000 + 2000) // Extra 2s for last explosions to finish

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      window.removeEventListener("resize", handleResize)
      clearInterval(launchInterval)
      clearTimeout(timeout)
    }
  }, [duration, intensity, colors, launch_count, particles_per_explosion])

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
        zIndex: z_index,
        overflow: "hidden",
      }}
    >
      <canvas 
        ref={canvasRef}
        style={{
          width: '100%',
          height: '100%',
          display: 'block'
        }}
      />
    </div>
  )
}

export default FireworksEffect
