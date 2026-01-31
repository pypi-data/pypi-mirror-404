/**
 * Canvas helper utilities for particle effects
 */

export function resizeCanvas(canvas: HTMLCanvasElement): void {
  // Get CSS dimensions from the canvas element itself (it's set to 100% via CSS)
  const rect = canvas.getBoundingClientRect()
  
  // Account for device pixel ratio for sharp rendering on retina displays
  const dpr = window.devicePixelRatio || 1
  
  // Set canvas internal resolution (backing store) - scaled for DPR
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  
  // Scale canvas drawing context to match device pixel ratio
  // This allows us to work with logical pixels in drawing code
  const ctx = canvas.getContext('2d')
  if (ctx) {
    ctx.scale(dpr, dpr)
  }
}

export function clearCanvas(ctx: CanvasRenderingContext2D, canvas: HTMLCanvasElement): void {
  ctx.clearRect(0, 0, canvas.width, canvas.height)
}

export function randomRange(min: number, max: number): number {
  return Math.random() * (max - min) + min
}

export function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

export function randomFromArray<T>(array: T[]): T {
  return array[Math.floor(Math.random() * array.length)]
}
