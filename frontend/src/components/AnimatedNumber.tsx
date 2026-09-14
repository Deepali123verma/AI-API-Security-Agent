import { useEffect, useState } from 'react'

interface AnimatedNumberProps {
  value: number
  durationMs?: number
  className?: string
}

export function AnimatedNumber({
  value,
  durationMs = 650,
  className = '',
}: AnimatedNumberProps) {
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    let frame = 0
    const start = performance.now()
    const from = 0
    const to = value

    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / durationMs)
      const eased = 1 - (1 - progress) ** 3
      setDisplay(Math.round(from + (to - from) * eased))
      if (progress < 1) {
        frame = requestAnimationFrame(tick)
      }
    }

    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [value, durationMs])

  return <span className={`tabular-nums ${className}`}>{display}</span>
}
