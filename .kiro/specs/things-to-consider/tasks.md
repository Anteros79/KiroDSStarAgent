# Implementation Plan: Things to Consider

## Overview

This implementation plan covers the "Things to Consider" feature - a guided query suggestion section with two tiles (Advice from the Field and Common Industry Causal Factors) that help station managers learn to effectively query DS-Star for causal analysis.

## Tasks

- [x] 1. Create industry factors configuration and types
  - [x] 1.1 Create types file with FieldAdviceSuggestion and IndustryFactor interfaces
    - Define TypeScript interfaces for suggestions and factors
    - Export types for use across components
    - _Requirements: 2.3, 3.3_

  - [x] 1.2 Create industryFactorsConfig.ts with factor definitions
    - Define INDUSTRY_FACTORS array with all factor categories
    - Include queryTemplate, relevantKpis, and priority for each factor
    - Implement getRelevantFactors(kpiId) function
    - _Requirements: 3.3, 3.5, 5.4, 5.5_

  - [x] 1.3 Write property test for KPI-specific factor relevance
    - **Property 2: KPI-specific factor relevance**
    - **Validates: Requirements 3.3, 3.5, 5.4, 5.5**

- [x] 2. Implement field advice prompt generation
  - [x] 2.1 Create fieldAdviceGenerator.ts with generateFieldAdvice function
    - Implement logic to generate prompts from diagnostics
    - Handle stage_change, yoy_delta, and peer_mean diagnostic types
    - Include station, KPI, and window context in generated queries
    - _Requirements: 2.3, 5.1, 5.2, 5.3_

  - [x] 2.2 Write property test for diagnostic-based prompt generation
    - **Property 1: Diagnostic-based prompt generation**
    - **Validates: Requirements 2.3, 5.1, 5.2, 5.3**

  - [x] 2.3 Write property test for query context inclusion
    - **Property 3: Query context inclusion**
    - **Validates: Requirements 4.3**

- [x] 3. Create SuggestionChip component
  - [x] 3.1 Implement SuggestionChip component
    - Create clickable chip with label and optional icon
    - Add loading state with spinner
    - Add hover and focus states
    - Include aria-label for accessibility
    - _Requirements: 2.6, 3.4, 4.4, 6.3, 6.4_

  - [x] 3.2 Write property test for accessibility labels
    - **Property 5: Accessibility labels**
    - **Validates: Requirements 6.4**

- [x] 4. Create tile components
  - [x] 4.1 Implement AdviceFromFieldTile component
    - Create tile with header, icon, and subtitle
    - Render SuggestionChip list from generated field advice
    - Handle empty state when no diagnostics available
    - Wire onClick to onSelectPrompt callback
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 4.2 Implement IndustryFactorsTile component
    - Create tile with header, icon, and subtitle
    - Render FactorChip list from relevant industry factors
    - Generate queries from factor templates with context interpolation
    - Wire onClick to onSelectFactor callback
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 5. Create ThingsToConsiderSection container
  - [x] 5.1 Implement ThingsToConsiderSection component
    - Create section with "Things to Consider" header
    - Stack AdviceFromFieldTile and IndustryFactorsTile vertically
    - Pass investigation context to child tiles
    - Handle onExecuteQuery callback to trigger DS-Star queries
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 4.2_

  - [x] 5.2 Write property test for click-to-execute behavior
    - **Property 4: Click-to-execute behavior**
    - **Validates: Requirements 4.1, 4.2**

- [x] 6. Integrate with InvestigationPage
  - [x] 6.1 Add ThingsToConsiderSection to InvestigationPage
    - Import and render ThingsToConsiderSection above InvestigationWorkbench
    - Pass investigation record, KPI, station, and window props
    - Connect onExecuteQuery to InvestigationWorkbench query execution
    - _Requirements: 1.1, 4.1, 4.2_

  - [x] 6.2 Wire query execution to InvestigationWorkbench
    - Create callback to populate query input and trigger execution
    - Handle loading state propagation
    - Handle error display for failed queries
    - _Requirements: 4.1, 4.2, 4.4, 4.5_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Add responsive styling
  - [x] 8.1 Add responsive CSS for mobile viewports
    - Stack tiles in single column on viewports < 768px
    - Ensure chips wrap properly on narrow screens
    - Maintain consistent spacing and padding
    - _Requirements: 1.4, 6.1, 6.5_

- [x] 9. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks including property-based tests are required
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The feature integrates with existing InvestigationWorkbench query execution flow
