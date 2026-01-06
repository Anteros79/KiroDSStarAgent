# Changelog

All notable changes to the DS-STAR Multi-Agent System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-06

### Added
- **Things to Consider Feature**: Guided query suggestions to help station managers learn effective DS-Star usage
  - `ThingsToConsiderSection` component with two vertically stacked tiles
  - `AdviceFromFieldTile` with dynamic suggestions based on investigation diagnostics
  - `IndustryFactorsTile` with standard industry causal factors
  - `SuggestionChip` component for clickable query suggestions
  - Field advice generation from stage changes, YoY deltas, and peer comparisons
  - Industry factors configuration with KPI-specific relevance and priority
  - Property-based testing for all new components and services

### Added - Responsive Design
- **Mobile-optimized layouts** for all Things to Consider components
- **Adaptive spacing and typography** that scales across device sizes
- **Touch-friendly suggestion chips** with proper sizing for mobile interaction
- **Single-column stacking** on viewports < 768px
- **Consistent visual hierarchy** maintained across all screen sizes

### Added - Testing
- Comprehensive property-based test suite using fast-check
- Unit tests for field advice generation logic
- Integration tests for click-to-execute behavior
- Accessibility testing for suggestion chips
- All tests passing with 100% coverage of new features

### Technical Details
- Added `fieldAdviceGenerator.ts` service for dynamic prompt generation
- Added `industryFactorsConfig.ts` with comprehensive factor definitions
- Integrated with existing InvestigationWorkbench query execution flow
- Implemented proper TypeScript interfaces and type safety
- Added responsive CSS classes using Tailwind CSS breakpoints

### Requirements Fulfilled
- ✅ Guided query suggestions section layout
- ✅ Dynamic field advice based on investigation findings
- ✅ Industry factors with KPI-specific relevance
- ✅ Click-to-execute query functionality
- ✅ Responsive design for mobile devices
- ✅ Accessibility compliance with ARIA labels
- ✅ Property-based testing for correctness validation

## [1.0.0] - 2026-01-04

### Added
- Initial release of DS-STAR Multi-Agent System
- Multi-provider LLM support (Lemonade, Anthropic, OpenAI, Ollama, Bedrock)
- Wheeler XmR Statistical Process Control implementation
- Tech Ops Dashboard with KPI visualization
- Investigation Workbench with multi-step analysis workflow
- Real-time WebSocket streaming for analysis updates
- Security audit module with secret scanning and dependency analysis
- Comprehensive test suite with pytest and Vitest
- Demo scenarios for presentations
- Generic LLM client for provider abstraction
- Session-based security with row-level access control

### Technical Stack
- **Backend**: Python, FastAPI, WebSockets, Pydantic
- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite
- **Testing**: pytest, Vitest, fast-check (property-based testing)
- **Charts**: Plotly.js for interactive visualizations
- **Security**: Custom audit tools for secrets, dependencies, and API endpoints
