import { describe, it, expect } from 'vitest'
import * as fc from 'fast-check'
import { getRelevantFactors, INDUSTRY_FACTORS } from './industryFactorsConfig'

describe('Industry Factors Configuration', () => {
  /**
   * Property 2: KPI-specific factor relevance
   * For any KPI identifier, the industry factors displayed should only include factors 
   * where the KPI is in the factor's relevantKpis list (or the factor applies to all KPIs), 
   * and factors should be sorted by priority (lower priority number first).
   * 
   * **Validates: Requirements 3.3, 3.5, 5.4, 5.5**
   */
  it('should return only relevant factors for any KPI and sort by priority', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 50 }), // Generate random KPI IDs
        (kpiId) => {
          const relevantFactors = getRelevantFactors(kpiId)
          
          // Property 1: All returned factors should be relevant to the KPI
          for (const factor of relevantFactors) {
            const isRelevant = factor.relevantKpis.includes('*') || factor.relevantKpis.includes(kpiId)
            expect(isRelevant).toBe(true)
          }
          
          // Property 2: Factors should be sorted by priority (ascending)
          for (let i = 1; i < relevantFactors.length; i++) {
            expect(relevantFactors[i - 1].priority).toBeLessThanOrEqual(relevantFactors[i].priority)
          }
          
          // Property 3: All universal factors (with '*') should be included
          const universalFactors = INDUSTRY_FACTORS.filter(f => f.relevantKpis.includes('*'))
          for (const universalFactor of universalFactors) {
            expect(relevantFactors).toContainEqual(universalFactor)
          }
        }
      ),
      { numRuns: 100 }
    )
  })

  it('should handle known KPI IDs correctly', () => {
    const knownKpis = ['otp_mx_ratio', 'dispatch_reliability', 'mttr', 'aog_rate']
    
    for (const kpiId of knownKpis) {
      const relevantFactors = getRelevantFactors(kpiId)
      
      // Should include at least universal factors
      expect(relevantFactors.length).toBeGreaterThan(0)
      
      // All factors should be relevant
      for (const factor of relevantFactors) {
        const isRelevant = factor.relevantKpis.includes('*') || factor.relevantKpis.includes(kpiId)
        expect(isRelevant).toBe(true)
      }
      
      // Should be sorted by priority
      for (let i = 1; i < relevantFactors.length; i++) {
        expect(relevantFactors[i - 1].priority).toBeLessThanOrEqual(relevantFactors[i].priority)
      }
    }
  })

  it('should return universal factors for any KPI', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 50 }),
        (kpiId) => {
          const relevantFactors = getRelevantFactors(kpiId)
          const universalFactors = INDUSTRY_FACTORS.filter(f => f.relevantKpis.includes('*'))
          
          // All universal factors should be present
          for (const universalFactor of universalFactors) {
            expect(relevantFactors.some(f => f.id === universalFactor.id)).toBe(true)
          }
        }
      ),
      { numRuns: 50 }
    )
  })
})