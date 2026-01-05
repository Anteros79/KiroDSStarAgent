# DS-STAR Demo Scenarios

## Overview
These scenarios demonstrate the DS-STAR system's ability to detect, analyze, and explain operational anomalies in airline tech ops metrics using Wheeler XmR statistical process control.

DS-STAR uses a star topology with an Orchestrator routing queries to 5 specialist agents:
- **Data Analyst** - Data exploration and KPI calculations
- **ML Engineer** - Predictive modeling recommendations
- **Visualization Expert** - Chart generation and visual analytics
- **Statistics Expert** - Wheeler XmR analysis and signal detection
- **Domain Expert** - Airline operations context and best practices

---

## Scenario 1: PHX Parts Shortage Impact on OTP
**Station:** PHX | **KPI:** OTP MX Rate | **Window:** Weekly

### The Story
Phoenix station experienced a significant spike in maintenance-related delays over the past 3 weeks. The OTP MX Rate jumped from 2.1% to 3.8%, breaching the upper control limit.

### What DS-STAR Detects
1. **Signal Characterization** (92% confidence)
   - Rule #1 violation: Value 3.8% exceeds UCL of 3.2%
   - Stage change detected at week -3

2. **Cross-Station Analysis** (95% confidence)
   - PHX isolated: 3.8%
   - DAL stable: 2.0%
   - HOU stable: 2.1%
   - Conclusion: Local issue, not systemic

3. **Root Cause Identified**
   - Parts shortage: Brake assembly P/N 2615400-5 backorder (12 days)

### Demo Steps
1. Navigate to Dashboard → Select PHX station
2. Click on OTP MX Rate card (shows critical signal)
3. Review diagnostic pills - note color-coded confidence levels
4. Expand "Signal Characterization" - shows Rule #1 violation
5. Expand "Cross Station" - shows PHX isolated from peers
6. Note the identified root cause in amber highlight

---

## Scenario 2: DAL Weather Cascade Effect
**Station:** DAL | **KPI:** MX Extreme Delay Rate | **Window:** Daily

### The Story
Dallas experienced severe thunderstorms over a 4-day period, triggering a cascade of maintenance-related extreme delays. The rate spiked to 1.8% (vs normal 0.9%).

### What DS-STAR Detects
1. **Signal Characterization** (89% confidence)
   - Rule #1 violation: 1.8% exceeds UCL of 1.4%
   - MR signal detected (high volatility)

2. **Cross-Station Analysis** (94% confidence)
   - Regional pattern identified
   - DAL: +0.9% spike
   - HOU: +0.4% (same region, less severe)
   - PHX: Stable (different region)

3. **Root Cause Identified**
   - Weather cascade: 4-day thunderstorm event disrupted overnight maintenance schedule

### Demo Steps
1. Navigate to Dashboard → Select DAL station
2. Switch to "Daily (30d)" view
3. Click on MX Extreme Delay Rate card
4. Review diagnostic pills - note the MR Signal flag
5. Expand "Cross Station" - shows regional pattern
6. Discuss weather contingency recommendations

---

## Scenario 3: Fleet-Wide Fault Rate Regression
**Station:** DAL (or any) | **KPI:** Fault Rate | **Window:** Weekly

### The Story
A company-wide increase in Fault Rate has been detected across all stations. The rate increased from 0.48 to 0.72 over 8 weeks. This is actually a "good news" signal - the EICAS software update introduced more sensitive fault detection.

### What DS-STAR Detects
1. **Signal Characterization** (95% confidence)
   - Stage change detected at week -8
   - New baseline established (not a spike)

2. **Cross-Station Analysis** (98% confidence)
   - All stations show parallel increase
   - DAL: +0.24
   - PHX: +0.24
   - HOU: +0.24
   - Conclusion: Systemic change, not local issue

3. **Root Cause Identified**
   - EICAS software update: Lowered fault detection thresholds (intentional)

### Demo Steps
1. Navigate to Dashboard → Select any station
2. Click on Fault Rate card
3. Note the "warning" signal (stage change, not critical spike)
4. Review diagnostic pills - note 98% confidence on cross-station
5. Expand "Pre/Post Shift" - shows sustained change
6. Discuss: This is a "good" signal - better detection, not worse performance

---

## Key Demo Talking Points

### Wheeler XmR Process Behavior Charts
- Natural Process Limits (NPL) calculated from data, not arbitrary thresholds
- Rule #1: Point beyond 3-sigma limits = special cause
- Stage changes detected automatically when process shifts

### Confidence-Based Diagnostics
- Color-coded pills: Green (85%+), Blue (65-84%), Amber (40-64%), Red (<40%)
- Each test shows specific metrics and findings
- Known root causes highlighted in amber

### Cross-Station Analysis
- Isolates local vs systemic issues
- Regional patterns detected automatically
- Peer comparison provides context

### Actionable Insights
- Root cause identification
- Recommended actions
- Evidence trail for audit

---

## Quick Reference: Diagnostic Test Colors

| Confidence | Color | Meaning |
|------------|-------|---------|
| 85%+ | Green | High confidence - strong signal |
| 65-84% | Blue | Medium confidence - likely signal |
| 40-64% | Amber | Low confidence - possible signal |
| <40% | Red | Very low confidence - weak signal |
