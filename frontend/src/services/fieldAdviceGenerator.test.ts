import { describe, it, expect } from 'vitest'
import * as fc from 'fast-check'
import { generateFieldAdvice } from './fieldAdviceGenerator'
import { InvestigationDiagnostic } from '../techops/types'

describe('Field Advice Generator', () => {
  /**
   * Property 1: Diagnostic-based prompt generation
   * For any set of investigation diagnostics containing stage changes, YoY deltas, 
   * or peer comparison data, the generated field advice prompts should include 
   * at least one suggestion relevant to each diagnostic finding type present.
   * 
   * **Validates: Requirements 2.3, 5.1, 5.2, 5.3**
   */
  it('should generate suggestions for each diagnostic finding type present', () => {
    fc.assert(
      fc.property(
        // Generate random KPI and station identifiers
        fc.string({ minLength: 3, maxLength: 20 }),
        fc.string({ minLength: 3, maxLength: 10 }),
        fc.constantFrom('weekly', 'daily'),
        // Generate diagnostics with different finding types
        fc.array(
          fc.record({
            name: fc.string({ minLength: 1, maxLength: 20 }),
            status: fc.constantFrom('pending', 'in_progress', 'completed', 'failed'),
            confidence: fc.option(fc.float({ min: 0, max: 1 }), { nil: undefined }),
            stage_change: fc.option(fc.boolean(), { nil: undefined }),
            yoy_delta: fc.option(fc.float({ min: -1, max: 1 }), { nil: undefined }),
            peer_mean: fc.option(fc.float({ min: 0, max: 1 }), { nil: undefined }),
            selected_value: fc.option(fc.float({ min: 0, max: 1 }), { nil: undefined }),
            selected_t: fc.option(fc.string(), { nil: undefined }),
            finding: fc.option(fc.string({ minLength: 1, maxLength: 100 }), { nil: undefined }),
          }),
          { minLength: 1, maxLength: 10 }
        ),
        (kpiId, station, window, diagnostics) => {
          const suggestions = generateFieldAdvice(diagnostics, kpiId, station, window)
          
          // Check if stage change diagnostics generate stage change suggestions
          const hasStageChange = diagnostics.some(d => d.stage_change === true)
          if (hasStageChange) {
            const hasStageChangeSuggestion = suggestions.some(s => s.source === 'stage_change')
            expect(hasStageChangeSuggestion).toBe(true)
          }
          
          // Check if significant YoY delta diagnostics generate YoY suggestions
          const hasSignificantYoY = diagnostics.some(d => 
            d.yoy_delta !== undefined && d.yoy_delta !== null && Math.abs(d.yoy_delta) > 0.05
          )
          if (hasSignificantYoY) {
            const hasYoYSuggestion = suggestions.some(s => s.source === 'yoy_delta')
            expect(hasYoYSuggestion).toBe(true)
          }
          
          // Check if peer comparison diagnostics generate peer comparison suggestions
          const hasPeerComparison = diagnostics.some(d => 
            d.peer_mean !== undefined && d.peer_mean !== null && 
            d.selected_value !== undefined && d.selected_value !== null &&
            Math.abs(d.selected_value - d.peer_mean) > 0.02
          )
          if (hasPeerComparison) {
            const hasPeerSuggestion = suggestions.some(s => s.source === 'peer_comparison')
            expect(hasPeerSuggestion).toBe(true)
          }
          
          // All suggestions should have valid IDs and queries
          for (const suggestion of suggestions) {
            expect(suggestion.id).toBeTruthy()
            expect(suggestion.query).toBeTruthy()
            expect(suggestion.label).toBeTruthy()
            expect(['stage_change', 'yoy_delta', 'peer_comparison', 'signal_pattern']).toContain(suggestion.source)
          }
          
          // Suggestions should be sorted by confidence (highest first)
          for (let i = 1; i < suggestions.length; i++) {
            const prevConfidence = suggestions[i - 1].confidence || 0
            const currentConfidence = suggestions[i].confidence || 0
            expect(prevConfidence).toBeGreaterThanOrEqual(currentConfidence)
          }
        }
      ),
      { numRuns: 100 }
    )
  })

  /**
   * Property 3: Query context inclusion
   * For any generated query (from field advice or industry factors), 
   * the query string should contain the station identifier, KPI identifier, 
   * and be contextually relevant to the investigation.
   * 
   * **Validates: Requirements 4.3**
   */
  it('should include context (station, KPI) in all generated queries', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 3, maxLength: 20 }),
        fc.string({ minLength: 3, maxLength: 10 }),
        fc.constantFrom('weekly', 'daily'),
        fc.array(
          fc.record({
            name: fc.string({ minLength: 1, maxLength: 20 }),
            status: fc.constantFrom('completed'),
            confidence: fc.float({ min: Math.fround(0.1), max: Math.fround(1) }),
            stage_change: fc.boolean(),
            yoy_delta: fc.float({ min: Math.fround(-0.5), max: Math.fround(0.5) }),
            peer_mean: fc.float({ min: Math.fround(0), max: Math.fround(1) }),
            selected_value: fc.float({ min: Math.fround(0), max: Math.fround(1) }),
            selected_t: fc.string({ minLength: 1, maxLength: 20 }),
            finding: fc.string({ minLength: 10, maxLength: 100 }),
          }),
          { minLength: 1, maxLength: 5 }
        ),
        (kpiId, station, window, diagnostics) => {
          const suggestions = generateFieldAdvice(diagnostics, kpiId, station, window)
          
          // Every generated query should contain the station and KPI identifiers
          for (const suggestion of suggestions) {
            expect(suggestion.query).toContain(station)
            expect(suggestion.query).toContain(kpiId)
            
            // Query should be a non-empty string
            expect(suggestion.query.length).toBeGreaterThan(0)
            
            // Query should be contextually relevant based on source
            switch (suggestion.source) {
              case 'stage_change':
                expect(suggestion.query.toLowerCase()).toMatch(/stage|change|shift/i)
                break
              case 'yoy_delta':
                expect(suggestion.query.toLowerCase()).toMatch(/year|yoy|compared/i)
                break
              case 'peer_comparison':
                expect(suggestion.query.toLowerCase()).toMatch(/peer|average|stations/i)
                break
              case 'signal_pattern':
                expect(suggestion.query.toLowerCase()).toMatch(/pattern|analysis|finding/i)
                break
            }
          }
        }
      ),
      { numRuns: 100 }
    )
  })

  // Unit test for specific examples
  it('should handle empty diagnostics array', () => {
    const suggestions = generateFieldAdvice([], 'test_kpi', 'TEST_STATION', 'weekly')
    expect(suggestions).toEqual([])
  })

  it('should generate stage change suggestion correctly', () => {
    const diagnostics: InvestigationDiagnostic[] = [{
      name: 'test_diagnostic',
      status: 'completed',
      confidence: 0.8,
      stage_change: true,
      selected_t: '2024-01-15'
    }]
    
    const suggestions = generateFieldAdvice(diagnostics, 'otp_ratio', 'LAX', 'weekly')
    
    expect(suggestions).toHaveLength(1)
    expect(suggestions[0].source).toBe('stage_change')
    expect(suggestions[0].query).toContain('LAX')
    expect(suggestions[0].query).toContain('otp_ratio')
    expect(suggestions[0].query).toContain('2024-01-15')
  })

  it('should generate YoY delta suggestion correctly', () => {
    const diagnostics: InvestigationDiagnostic[] = [{
      name: 'test_diagnostic',
      status: 'completed',
      confidence: 0.9,
      yoy_delta: 0.15 // 15% increase
    }]
    
    const suggestions = generateFieldAdvice(diagnostics, 'dispatch_reliability', 'JFK', 'daily')
    
    expect(suggestions).toHaveLength(1)
    expect(suggestions[0].source).toBe('yoy_delta')
    expect(suggestions[0].query).toContain('JFK')
    expect(suggestions[0].query).toContain('dispatch_reliability')
    expect(suggestions[0].query).toContain('15.0%')
    expect(suggestions[0].query).toContain('increase')
  })

  it('should generate peer comparison suggestion correctly', () => {
    const diagnostics: InvestigationDiagnostic[] = [{
      name: 'test_diagnostic',
      status: 'completed',
      confidence: 0.7,
      peer_mean: 0.85,
      selected_value: 0.75 // Below peer average
    }]
    
    const suggestions = generateFieldAdvice(diagnostics, 'mttr', 'ORD', 'weekly')
    
    expect(suggestions).toHaveLength(1)
    expect(suggestions[0].source).toBe('peer_comparison')
    expect(suggestions[0].query).toContain('ORD')
    expect(suggestions[0].query).toContain('mttr')
    expect(suggestions[0].query).toContain('below')
  })
})