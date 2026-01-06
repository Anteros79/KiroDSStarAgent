# Implementation Plan: Security Audit & Hardening

## Overview

This implementation plan breaks down the security audit system into discrete coding tasks. The approach builds incrementally: data models first, then individual scanners, followed by the report generator, and finally integration with annotation injection.

## Tasks

- [x] 1. Set up project structure and data models
  - Create `src/security/` directory structure
  - Define data models (SecurityFinding, Severity, FindingCategory, etc.)
  - Set up testing framework with hypothesis
  - _Requirements: 1.2, 2.3, 3.5, 4.3_

- [x] 2. Implement Secret Scanner
  - [x] 2.1 Create secret pattern matching engine
    - Implement regex patterns for API keys, AWS credentials, passwords, tokens, private keys, JWTs, connection strings
    - Implement file traversal with exclusion patterns (.git, node_modules, .venv, etc.)
    - Implement secret masking function
    - _Requirements: 1.1, 1.2, 1.4_

  - [ ]* 2.2 Write property test for secret masking integrity
    - **Property 2: Secret Masking Integrity**
    - **Validates: Requirements 1.2, 1.4**

  - [x] 2.3 Implement secret scanning orchestration
    - Scan all source files in repository
    - Aggregate findings by type and severity
    - Generate summary counts
    - _Requirements: 1.1, 1.3_

  - [ ]* 2.4 Write property test for secret detection completeness
    - **Property 1: Secret Detection Completeness**
    - **Validates: Requirements 1.1**

  - [ ]* 2.5 Write property test for summary count accuracy
    - **Property 3: Summary Count Accuracy**
    - **Validates: Requirements 1.3**

- [x] 3. Checkpoint - Ensure secret scanner tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement Dependency Analyzer
  - [x] 4.1 Create dependency file parsers
    - Implement requirements.txt parser
    - Implement package.json parser
    - Handle missing files gracefully with warnings
    - _Requirements: 2.1, 2.4_

  - [x] 4.2 Implement CVE lookup integration
    - Integrate with pip-audit for Python packages
    - Integrate with npm-audit for Node packages
    - Record CVE details (ID, severity, safe version)
    - _Requirements: 2.2, 2.3_

  - [ ]* 4.3 Write property test for dependency parsing completeness
    - **Property 4: Dependency Parsing Completeness**
    - **Validates: Requirements 2.1, 2.2**

  - [ ]* 4.4 Write property test for CVE finding structure
    - **Property 5: CVE Finding Structure**
    - **Validates: Requirements 2.3**

- [x] 5. Checkpoint - Ensure dependency analyzer tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement API Auditor
  - [x] 6.1 Create endpoint detection engine
    - Implement FastAPI endpoint pattern matching (@app.get, @router.post, etc.)
    - Implement Flask endpoint pattern matching (@app.route, @blueprint.route)
    - Implement Express endpoint pattern matching (app.get, router.post)
    - _Requirements: 3.1_

  - [x] 6.2 Implement authorization checker
    - Detect presence of auth middleware/decorators (Depends, @login_required, @jwt_required)
    - Flag endpoints missing authorization controls
    - _Requirements: 3.2_

  - [x] 6.3 Implement input validation checker
    - Detect unvalidated request data access patterns
    - Detect potential injection risks (exec, eval, subprocess, os.system)
    - Classify findings by OWASP Top 10 category
    - _Requirements: 3.3, 3.4_

  - [ ]* 6.4 Write property test for API endpoint analysis completeness
    - **Property 6: API Endpoint Analysis Completeness**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

- [x] 7. Checkpoint - Ensure API auditor tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement Report Generator
  - [x] 8.1 Create executive summary generator
    - Calculate overall risk assessment
    - Generate key metrics (total findings, by severity, by category)
    - _Requirements: 4.2_

  - [x] 8.2 Create critical findings table generator
    - Generate markdown table with ID, Category, Severity, Location, Description columns
    - Sort findings by severity (Critical > High > Medium > Low)
    - _Requirements: 4.3, 4.5_

  - [x] 8.3 Create remediation plan generator
    - Generate prioritized action items
    - Include estimated effort for each remediation
    - _Requirements: 4.4_

  - [x] 8.4 Implement SECURITY_AUDIT.md file writer
    - Combine all sections into final report
    - Write to repository root directory
    - _Requirements: 4.1_

  - [ ]* 8.5 Write property test for report structure completeness
    - **Property 7: Report Structure Completeness**
    - **Validates: Requirements 4.2, 4.3, 4.4**

  - [ ]* 8.6 Write property test for findings severity ordering
    - **Property 8: Findings Severity Ordering**
    - **Validates: Requirements 4.5**

- [x] 9. Checkpoint - Ensure report generator tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Implement Annotation Injector
  - [x] 10.1 Create annotation injection engine
    - Add `// TODO: SECURITY CRITICAL` comments for critical findings
    - Preserve original file content (non-destructive)
    - Log annotations in report
    - _Requirements: 5.1, 5.2, 5.3, 5.5_

  - [x] 10.2 Implement test verification and rollback
    - Run existing tests after annotation
    - Revert annotations if tests fail
    - Log conflicts in report
    - _Requirements: 5.4, 6.2, 6.3, 6.4_

  - [ ]* 10.3 Write property test for critical finding annotation
    - **Property 9: Critical Finding Annotation**
    - **Validates: Requirements 5.1, 5.5**

  - [ ]* 10.4 Write property test for non-destructive operation
    - **Property 10: Non-Destructive Operation**
    - **Validates: Requirements 5.2, 5.3, 6.1**

- [x] 11. Implement Main Security Scanner Orchestrator
  - [x] 11.1 Create main orchestrator class
    - Coordinate all scanning phases
    - Aggregate findings from all scanners
    - Trigger report generation
    - _Requirements: 1.1, 2.1, 3.1, 4.1_

  - [x] 11.2 Create CLI entry point
    - Accept repository root path argument
    - Support dry-run mode (no annotations)
    - Output summary to console
    - _Requirements: 4.1_

- [x] 12. Final checkpoint - Run full audit on codebase
  - Ensure all tests pass, ask the user if questions arise.
  - Execute full security audit on the current repository
  - Review generated SECURITY_AUDIT.md

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation uses Python with pytest and hypothesis for testing
