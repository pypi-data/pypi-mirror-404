import React, { useEffect, useRef } from "react"
import { MatrixEffectProps } from "../utils/types"
import { resizeCanvas, randomInt } from "../utils/canvasHelpers"

interface MatrixColumn {
  x: number
  y: number
  speed: number
  chars: string[]
}

const MatrixEffect: React.FC<MatrixEffectProps> = ({
  intensity,
  speed,
  color,
  font_size,
  column_density,
  z_index,
  duration,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const columnsRef = useRef<MatrixColumn[]>([])
  const animationRef = useRef<number>()

  // Matrix character set
  const matrixChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@#$%^&*()ｦｱｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ"

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    const handleResize = () => {
      resizeCanvas(canvas)
      initializeColumns()
    }
    handleResize()
    window.addEventListener("resize", handleResize)

    // Initialize columns
    const initializeColumns = () => {
      const displayWidth = canvas.clientWidth
      const displayHeight = canvas.clientHeight
      const columnCount = Math.floor((displayWidth / font_size) * column_density)
      columnsRef.current = []

      for (let i = 0; i < columnCount; i++) {
        const column: MatrixColumn = {
          x: randomInt(0, Math.floor(displayWidth / font_size)) * font_size,
          y: randomInt(-displayHeight, 0),
          speed: randomInt(1, 3),
          chars: Array.from({ length: 20 }, () => 
            matrixChars[randomInt(0, matrixChars.length - 1)]
          ),
        }
        columnsRef.current.push(column)
      }
    }

    initializeColumns()

    // Animation loop
    const animate = () => {
      const displayWidth = canvas.clientWidth
      const displayHeight = canvas.clientHeight
      
      // Fade effect for trail
      ctx.fillStyle = "rgba(0, 0, 0, 0.05)"
      ctx.fillRect(0, 0, displayWidth, displayHeight)

      ctx.fillStyle = color
      ctx.font = `${font_size}px monospace`

      columnsRef.current.forEach((column) => {
        // Draw characters in column
        column.chars.forEach((char, index) => {
          const y = column.y + index * font_size
          if (y > 0 && y < displayHeight) {
            // Brightest at the head
            const alpha = index === 0 ? 1.0 : 1.0 - (index / column.chars.length)
            ctx.globalAlpha = alpha
            ctx.fillText(char, column.x, y)
          }
        })

        // Move column down
        column.y += column.speed * speed

        // Randomly update characters
        if (Math.random() > 0.98) {
          const randIndex = randomInt(0, column.chars.length - 1)
          column.chars[randIndex] = matrixChars[randomInt(0, matrixChars.length - 1)]
        }

        // Reset column if off screen
        if (column.y - column.chars.length * font_size > displayHeight) {
          column.y = -column.chars.length * font_size
          column.x = randomInt(0, Math.floor(displayWidth / font_size)) * font_size
        }
      })

      ctx.globalAlpha = 1.0
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
  }, [intensity, speed, color, font_size, column_density, duration])

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
        backgroundColor: "black",
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

export default MatrixEffect
