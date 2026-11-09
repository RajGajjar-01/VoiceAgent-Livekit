import { describe, expect, it } from 'vitest'
import { cn, formatDuration } from './utils'

describe('cn', () => {
  it('merges conflicting tailwind classes', () => {
    expect(cn('p-2', 'p-4')).toBe('p-4')
  })
})

describe('formatDuration', () => {
  const at = (m: number) => new Date(Date.UTC(2026, 0, 1, 0, m)).toISOString()
  it('formats minutes and hours', () => {
    expect(formatDuration(at(0), at(0))).toBe('<1 min')
    expect(formatDuration(at(0), at(45))).toBe('45 min')
    expect(formatDuration(at(0), at(60))).toBe('1 hr')
    expect(formatDuration(at(0), at(90))).toBe('1 hr 30 min')
  })
})
