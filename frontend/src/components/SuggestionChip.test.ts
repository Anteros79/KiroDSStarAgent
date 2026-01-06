import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import { SuggestionChip } from './SuggestionChip'
import * as fc from 'fast-check'

describe('SuggestionChip', () => {
  describe('Property 5: Accessibility labels', () => {
    it('should have aria-label that describes the action for any query', () => {
      /**
       * Feature: things-to-consider, Property 5: Accessibility labels
       * Validates: Requirements 6.4
       */
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 100 }), // label
          fc.string({ minLength: 1, maxLength: 500 }), // query
          (label, query) => {
            const mockOnClick = vi.fn()
            
            const { container } = render(
              SuggestionChip({
                label,
                query,
                onClick: mockOnClick,
              })
            )
            
            const button = container.querySelector('button')
            expect(button).toBeTruthy()
            
            const ariaLabel = button?.getAttribute('aria-label')
            expect(ariaLabel).toBeTruthy()
            expect(ariaLabel).toContain('Run query:')
            expect(ariaLabel).toContain(query)
          }
        ),
        { numRuns: 100 }
      )
    })
  })
})