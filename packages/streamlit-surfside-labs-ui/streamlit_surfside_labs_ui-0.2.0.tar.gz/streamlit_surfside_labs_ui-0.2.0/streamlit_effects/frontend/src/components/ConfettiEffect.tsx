import React, { useEffect, useRef } from "react"
import { ConfettiEffectProps } from "../utils/types"
import { ParticleSystem } from "../utils/particleSystem"
import { resizeCanvas, randomRange, randomFromArray } from "../utils/canvasHelpers"

const ConfettiEffect: React.FC<ConfettiEffectProps> = ({
  duration,
  particle_count,
  colors,
  spread,
  origin_x,
  origin_y,
  velocity,
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

    // Launch confetti using logical display dimensions
    const launchConfetti = () => {
      const displayWidth = canvas.clientWidth
      const displayHeight = canvas.clientHeight
      const originX = displayWidth * origin_x
      const originY = displayHeight * origin_y

      for (let i = 0; i < particle_count; i++) {
        const angle = randomRange(0, spread) * (Math.PI / 180) - spread / 2 * (Math.PI / 180)
        const speed = randomRange(velocity * 0.5, velocity)

        particleSystemRef.current!.addParticle({
          x: originX,
          y: originY,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed - 5, // Initial upward force
          size: randomRange(5, 10),
          color: randomFromArray(colors),
          opacity: 1.0,
          rotation: randomRange(0, Math.PI * 2),
          rotationSpeed: randomRange(-0.1, 0.1),
        })
      }
    }

    launchConfetti()

    // Animation loop with gravity
    const animate = () => {
      const displayWidth = canvas.clientWidth
      const displayHeight = canvas.clientHeight
      ctx.clearRect(0, 0, displayWidth, displayHeight)

      // Apply gravity
      particleSystemRef.current!.particles.forEach((p) => {
        p.vy += 0.3 // Gravity
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
    }, duration * 1000)

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      window.removeEventListener("resize", handleResize)
      clearTimeout(timeout)
    }
  }, [duration, particle_count, colors, spread, origin_x, origin_y, velocity])

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

export default ConfettiEffect
