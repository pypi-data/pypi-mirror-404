import React, { useEffect, useRef } from "react"
import { SnowEffectProps } from "../utils/types"
import { resizeCanvas, randomRange, randomInt } from "../utils/canvasHelpers"

interface Snowflake {
  x: number
  y: number
  size: number
  speedY: number
  speedX: number
  opacity: number
}

const SnowEffect: React.FC<SnowEffectProps> = ({
  intensity,
  speed,
  color,
  particle_count,
  z_index,
  duration,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const snowflakesRef = useRef<Snowflake[]>([])
  const animationRef = useRef<number>()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    // Resize canvas to fill container (using CSS dimensions)
    const handleResize = () => {
      resizeCanvas(canvas)
      // After resize, reinitialize particles with new dimensions
      const displayWidth = canvas.clientWidth
      const displayHeight = canvas.clientHeight
      snowflakesRef.current = snowflakesRef.current.map(flake => ({
        ...flake,
        x: Math.min(flake.x, displayWidth),
        y: Math.min(flake.y, displayHeight)
      }))
    }
    handleResize()
    window.addEventListener("resize", handleResize)

    // Get logical display dimensions (not DPR-scaled)
    const displayWidth = canvas.clientWidth
    const displayHeight = canvas.clientHeight

    // Initialize snowflakes using display dimensions
    snowflakesRef.current = Array.from({ length: particle_count }, () => ({
      x: randomRange(0, displayWidth),
      y: randomRange(-displayHeight, 0),
      size: randomRange(2, 5),
      speedY: randomRange(0.5, 1.5),
      speedX: randomRange(-0.3, 0.3),
      opacity: randomRange(0.3, 1.0),
    }))

    // Animation loop
    const animate = () => {
      // Use logical display dimensions for clearing
      const displayWidth = canvas.clientWidth
      const displayHeight = canvas.clientHeight
      ctx.clearRect(0, 0, displayWidth, displayHeight)
      ctx.fillStyle = color

      snowflakesRef.current.forEach((flake) => {
        ctx.globalAlpha = flake.opacity
        ctx.beginPath()
        ctx.arc(flake.x, flake.y, flake.size, 0, Math.PI * 2)
        ctx.fill()

        // Update position
        flake.y += flake.speedY * speed
        flake.x += flake.speedX * speed

        // Reset if off screen (use display dimensions)
        if (flake.y > displayHeight + 10) {
          flake.y = -10
          flake.x = randomRange(0, displayWidth)
        }
        if (flake.x > displayWidth + 10) flake.x = 0
        if (flake.x < -10) flake.x = displayWidth
      })

      animationRef.current = requestAnimationFrame(animate)
    }
    animate()

    // Auto-stop after duration
    let timeout: NodeJS.Timeout | undefined
    if (duration) {
      timeout = setTimeout(() => {
        if (animationRef.current) {
          cancelAnimationFrame(animationRef.current)
        }
      }, duration * 1000)
    }

    // Cleanup
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      window.removeEventListener("resize", handleResize)
      if (timeout) clearTimeout(timeout)
    }
  }, [intensity, speed, color, particle_count, duration])

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

export default SnowEffect
