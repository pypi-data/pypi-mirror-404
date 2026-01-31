import React, { useEffect, useRef } from "react"
import { HeartsEffectProps } from "../utils/types"
import { resizeCanvas, randomRange, randomFromArray } from "../utils/canvasHelpers"

interface Heart {
  x: number
  y: number
  size: number
  speedY: number
  speedX: number
  opacity: number
  color: string
}

const HeartsEffect: React.FC<HeartsEffectProps> = ({
  intensity,
  speed,
  colors,
  particle_count,
  z_index,
  duration,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const heartsRef = useRef<Heart[]>([])
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

    // Initialize hearts at bottom using logical display dimensions
    const displayWidth = canvas.clientWidth
    const displayHeight = canvas.clientHeight
    heartsRef.current = Array.from({ length: particle_count }, () => ({
      x: randomRange(0, displayWidth),
      y: displayHeight + randomRange(0, 100),
      size: randomRange(15, 30),
      speedY: randomRange(1, 2), // Negative for upward movement
      speedX: randomRange(-0.5, 0.5), // Gentle drift
      opacity: randomRange(0.6, 1.0),
      color: randomFromArray(colors),
    }))

    // Draw heart shape
    const drawHeart = (ctx: CanvasRenderingContext2D, x: number, y: number, size: number, color: string, opacity: number) => {
      ctx.save()
      ctx.globalAlpha = opacity
      ctx.fillStyle = color
      ctx.beginPath()
      
      const topCurveHeight = size * 0.3
      ctx.moveTo(x, y + topCurveHeight)
      
      // Left half of heart
      ctx.bezierCurveTo(
        x, y, 
        x - size / 2, y, 
        x - size / 2, y + topCurveHeight
      )
      ctx.bezierCurveTo(
        x - size / 2, y + (size + topCurveHeight) / 2, 
        x, y + (size + topCurveHeight) / 2, 
        x, y + size
      )
      
      // Right half of heart
      ctx.bezierCurveTo(
        x, y + (size + topCurveHeight) / 2, 
        x + size / 2, y + (size + topCurveHeight) / 2, 
        x + size / 2, y + topCurveHeight
      )
      ctx.bezierCurveTo(
        x + size / 2, y, 
        x, y, 
        x, y + topCurveHeight
      )
      
      ctx.closePath()
      ctx.fill()
      ctx.restore()
    }

    // Animation loop
    const animate = () => {
      const displayWidth = canvas.clientWidth
      const displayHeight = canvas.clientHeight
      ctx.clearRect(0, 0, displayWidth, displayHeight)

      heartsRef.current.forEach((heart) => {
        drawHeart(ctx, heart.x, heart.y, heart.size, heart.color, heart.opacity)

        // Float upward
        heart.y -= heart.speedY * speed
        heart.x += heart.speedX * speed

        // Gentle oscillation
        heart.x += Math.sin(heart.y / 30) * 0.5

        // Fade out as it rises
        if (heart.y < displayHeight * 0.3) {
          heart.opacity -= 0.005
        }

        // Reset if off screen
        if (heart.y < -heart.size || heart.opacity <= 0) {
          heart.y = displayHeight + heart.size
          heart.x = randomRange(0, displayWidth)
          heart.opacity = randomRange(0.6, 1.0)
          heart.color = randomFromArray(colors)
        }
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

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      window.removeEventListener("resize", handleResize)
      if (timeout) clearTimeout(timeout)
    }
  }, [intensity, speed, colors, particle_count, duration])

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

export default HeartsEffect
