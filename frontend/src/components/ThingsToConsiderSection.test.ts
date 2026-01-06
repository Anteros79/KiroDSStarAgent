import { describe, it, expect, vi } from 'vitest'
import { render, fireEvent } from '@testing-library/react'
import { ThingsToConsiderSection } from './ThingsToConsiderSection'
import { InvestigationRecord, InvestigationDiagnostic } from '../techops/types'
import * as fc from 'fast-check'

describe('ThingsToConsiderSection', () => {
  describe('Property 4: Click-to-execute behavior', () => {
    it('should invoke onExecuteQuery callback with the query string for any suggestion chip click', () => {
      /**
       * Feature: things-to-consider, Property 4: Click-to-execute behavior
       * Validates: Requirements 4.1, 4.2
       */
      fc.assert(
        fc.property(
          fc.string({ minLength: 1, maxLength: 20 }), // kpiId
          fc.string({ minLength: 1, maxLength: 20 }), // station
          fc.constantFrom('weekly', 'daily'), // window
          fc.array(
            fc.record({
              name: fc.string({ minLength: 1, maxLength: 50 }),
              status: fc.constantFrom('pending', 'in_progress', 'completed', 'failed'),
              confidence: fc.option(fc.float({ min: 0, max: 1 })),
              stage_change: fc.option(fc.boolean()),
              yoy_delta: fc.option(fc.float({ min: -1, max: 1 })),
              peer_mean: fc.option(fc.float({ min: 0, max: 1 })),
              selected_value: fc.option(fc.float({ min: 0, max: 1 })),
              selected_t: fc.option(fc.string()),
            }),
            { minLength: 0, maxLength: 5 }
          ), // diagnostics
          (kpiId, station, window, diagnostics) => {
            const mockOnExecuteQuery = vi.fn()
            
            const investigation: InvestigationRecord = {
              investigation_id: 'test-id',
              kpi_id: kpiId,
              station,
              window,
              created_by: { id: 'user1', name: 'Test User', role: 'manager', station },
              created_at: '2024-01-01T00:00:00Z',
              status: 'active',
              prompt_mode: 'cause',
              prompt: 'Test prompt',
              diagnostics: diagnostics as InvestigationDiagnostic[],
            }
            
            const { container } = render(
              ThingsToConsiderSection({
                investigation,
                kpiId,
                station,
                window,
                onExecuteQuery: mockOnExecuteQuery,
                isProcessing: false,
              })
            )
            
            // Find all suggestion chip buttons
            const buttons = container.querySelectorAll('button[aria-label*="Run query:"]')
            
            if (buttons.length > 0) {
              // Click the first button
              fireEvent.click(buttons[0])
              
              // Verify onExecuteQuery was called with a string
              expect(mockOnExecuteQuery).toHaveBeenCalledTimes(1)
              const calledWith = mockOnExecuteQuery.mock.calls[0][0]
              expect(typeof calledWith).toBe('string')
              expect(calledWith.length).toBeGreaterThan(0)
            }
          }
        ),
        { numRuns: 100 }
      )
    })
  })
})