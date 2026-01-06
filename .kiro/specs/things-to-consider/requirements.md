# Requirements Document

## Introduction

This document specifies the requirements for a "Things to Consider" section in the DS-Star TechOps investigation interface. The feature provides two vertically stacked tiles that help station managers learn how to effectively query the DS-Star engine for causal analysis. The first tile displays "Advice from the Field" - suggested queries based on investigation findings and similar conditions from other stations. The second tile displays "Common Industry Causal Factors" - standard industry factors that should be checked during root cause analysis. Both tiles generate and execute DS-Star queries when clicked.

## Glossary

- **Things_to_Consider_Section**: A UI section containing two vertically stacked tiles for guided query suggestions
- **Advice_from_Field_Tile**: A tile displaying suggested queries derived from investigation findings and similar signals from other stations
- **Industry_Factors_Tile**: A tile displaying common industry causal factors that can be checked via DS-Star queries
- **Suggested_Prompt**: A clickable query suggestion that populates and executes in the DS-Star query interface
- **Investigation_Context**: The current investigation's KPI, station, window, diagnostics, and findings
- **Similar_Conditions**: Signals or patterns from other stations that match the current investigation's characteristics

## Requirements

### Requirement 1: Things to Consider Section Layout

**User Story:** As a station manager, I want to see a dedicated section with guided query suggestions, so that I can learn how to effectively use DS-Star for causal analysis.

#### Acceptance Criteria

1. WHEN the InvestigationPage loads THEN the Things_to_Consider_Section SHALL display near the top of the page, above the InvestigationWorkbench
2. WHEN the Things_to_Consider_Section renders THEN it SHALL display a section header titled "Things to Consider"
3. WHEN the Things_to_Consider_Section renders THEN it SHALL contain two tiles stacked vertically
4. WHEN the viewport width is less than 768px THEN the tiles SHALL stack in a single column with full width

### Requirement 2: Advice from the Field Tile

**User Story:** As a station manager, I want to see suggestions based on findings from similar conditions at other stations, so that I can learn from field experience.

#### Acceptance Criteria

1. WHEN the Advice_from_Field_Tile renders THEN it SHALL display a header with title "Advice from the Field" and a lightbulb icon
2. WHEN the Advice_from_Field_Tile renders THEN it SHALL display a subtitle explaining these are suggestions based on similar conditions from other stations
3. WHEN investigation diagnostics are available THEN the Advice_from_Field_Tile SHALL generate suggested prompts based on the diagnostic findings
4. WHEN similar signals exist at other stations THEN the Advice_from_Field_Tile SHALL include prompts to compare with those stations
5. WHEN no diagnostics or similar conditions exist THEN the Advice_from_Field_Tile SHALL display a message indicating no field suggestions are available
6. WHEN a suggested prompt is displayed THEN it SHALL appear as a clickable chip/button with the query text

### Requirement 3: Common Industry Causal Factors Tile

**User Story:** As a station manager, I want to see common industry factors to check, so that I can systematically investigate potential root causes.

#### Acceptance Criteria

1. WHEN the Industry_Factors_Tile renders THEN it SHALL display a header with title "Common Industry Causal Factors" and a clipboard/checklist icon
2. WHEN the Industry_Factors_Tile renders THEN it SHALL display a subtitle explaining these are standard factors to check during root cause analysis
3. WHEN the Industry_Factors_Tile renders THEN it SHALL display a list of common causal factor categories relevant to the current KPI
4. WHEN a causal factor is displayed THEN it SHALL appear as a clickable chip/button that generates an appropriate DS-Star query
5. WHEN the current KPI is known THEN the Industry_Factors_Tile SHALL prioritize factors most relevant to that KPI type

### Requirement 4: Query Generation and Execution

**User Story:** As a station manager, I want clicking a suggestion to automatically query DS-Star, so that I can quickly explore the suggested analysis.

#### Acceptance Criteria

1. WHEN a user clicks a suggested prompt chip THEN the system SHALL populate the DS-Star query input with the generated query text
2. WHEN a user clicks a suggested prompt chip THEN the system SHALL automatically execute the query in DS-Star
3. WHEN a query is generated THEN it SHALL include relevant context from the current investigation (station, KPI, time window)
4. WHEN a query is executing THEN the clicked chip SHALL display a loading indicator
5. IF a query execution fails THEN the system SHALL display an error message and allow retry

### Requirement 5: Dynamic Suggestion Generation

**User Story:** As a station manager, I want suggestions that are relevant to my specific investigation, so that the guidance is actionable.

#### Acceptance Criteria

1. WHEN diagnostics indicate a stage change THEN the Advice_from_Field_Tile SHALL suggest queries about what changed at that time
2. WHEN diagnostics indicate a YoY delta THEN the Advice_from_Field_Tile SHALL suggest queries comparing year-over-year patterns
3. WHEN diagnostics show peer comparison data THEN the Advice_from_Field_Tile SHALL suggest queries about peer station differences
4. WHEN the KPI relates to on-time performance THEN the Industry_Factors_Tile SHALL include factors like weather, staffing, equipment, and scheduling
5. WHEN the KPI relates to maintenance metrics THEN the Industry_Factors_Tile SHALL include factors like parts availability, technician training, and fleet age

### Requirement 6: Visual Design and Accessibility

**User Story:** As a user, I want the suggestions section to be visually clear and accessible, so that I can easily understand and interact with it.

#### Acceptance Criteria

1. WHEN tiles are displayed THEN they SHALL have consistent styling with the existing card components (rounded corners, subtle shadows, proper spacing)
2. WHEN suggestion chips are displayed THEN they SHALL have hover states indicating they are clickable
3. WHEN a chip is focused via keyboard THEN it SHALL display a visible focus indicator
4. WHEN chips are displayed THEN they SHALL include appropriate aria-labels describing their action
5. WHEN the section loads THEN it SHALL not cause layout shift in the existing page content
