import { IndustryFactor } from '../types/thingsToConsider'

export const INDUSTRY_FACTORS: IndustryFactor[] = [
  // Weather & Environmental
  {
    id: 'weather_impact',
    category: 'Environmental',
    label: 'Weather Impact',
    description: 'Analyze weather-related delays and disruptions',
    queryTemplate: 'Analyze weather impact on {kpi} at {station}. Were there severe weather events during the signal period?',
    relevantKpis: ['otp_mx_ratio', 'dispatch_reliability', 'cancellation_rate', 'completion_factor'],
    priority: 1,
  },
  // Staffing & Resources
  {
    id: 'staffing_levels',
    category: 'Resources',
    label: 'Staffing Levels',
    description: 'Check maintenance crew availability and scheduling',
    queryTemplate: 'Analyze staffing levels at {station} during the signal period. Were there crew shortages or scheduling issues?',
    relevantKpis: ['otp_mx_ratio', 'mttr', 'dispatch_reliability'],
    priority: 2,
  },
  // Equipment & Fleet
  {
    id: 'fleet_age',
    category: 'Fleet',
    label: 'Fleet Age Analysis',
    description: 'Examine aircraft age and reliability correlation',
    queryTemplate: 'Is there correlation between aircraft age and {kpi} issues at {station}? Compare older vs newer fleet.',
    relevantKpis: ['dispatch_reliability', 'mtbf', 'aog_rate', 'otp_mx_ratio'],
    priority: 3,
  },
  // Parts & Supply Chain
  {
    id: 'parts_availability',
    category: 'Supply Chain',
    label: 'Parts Availability',
    description: 'Check parts stockouts and supply chain issues',
    queryTemplate: 'Were there parts availability issues at {station} during the signal period? Which parts caused delays?',
    relevantKpis: ['mttr', 'aog_rate', 'dispatch_reliability', 'otp_mx_ratio'],
    priority: 2,
  },
  // Process & Procedures
  {
    id: 'procedure_changes',
    category: 'Process',
    label: 'Procedure Changes',
    description: 'Check for recent process or procedure changes',
    queryTemplate: 'Were there any procedure or process changes at {station} that coincide with the {kpi} signal?',
    relevantKpis: ['*'], // Relevant to all KPIs
    priority: 4,
  },
  // Training & Competency
  {
    id: 'training_gaps',
    category: 'Training',
    label: 'Training & Competency',
    description: 'Analyze technician training and skill gaps',
    queryTemplate: 'Are there training or competency gaps at {station} that could explain the {kpi} degradation?',
    relevantKpis: ['mttr', 'dispatch_reliability', 'otp_mx_ratio'],
    priority: 3,
  },
  // Vendor & External
  {
    id: 'vendor_performance',
    category: 'External',
    label: 'Vendor Performance',
    description: 'Check third-party vendor and supplier issues',
    queryTemplate: 'Were there vendor or supplier performance issues affecting {kpi} at {station}?',
    relevantKpis: ['parts_availability', 'mttr', 'aog_rate'],
    priority: 4,
  },
  // Scheduling & Planning
  {
    id: 'schedule_changes',
    category: 'Planning',
    label: 'Schedule Changes',
    description: 'Analyze flight schedule or maintenance schedule changes',
    queryTemplate: 'Were there schedule changes at {station} that impacted {kpi}? Compare before and after schedules.',
    relevantKpis: ['otp_mx_ratio', 'utilization', 'completion_factor'],
    priority: 3,
  },
]

/**
 * Get industry factors relevant to a specific KPI
 * @param kpiId - The KPI identifier to filter factors for
 * @returns Array of relevant industry factors sorted by priority
 */
export function getRelevantFactors(kpiId: string): IndustryFactor[] {
  return INDUSTRY_FACTORS
    .filter(factor => 
      factor.relevantKpis.includes('*') || 
      factor.relevantKpis.includes(kpiId)
    )
    .sort((a, b) => a.priority - b.priority)
}