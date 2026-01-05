/**
 * Measure-specific configuration for Tech Ops KPI investigations.
 * Each measure has tailored descriptions, analysis options, and related measures.
 */

export interface MeasureAnalysisOption {
  id: string
  label: string
  description: string
  suggestedQuery: string
}

export interface MeasureConfig {
  id: string
  label: string
  unit: string
  /** What this measure tracks and why it matters */
  description: string
  /** What a signal (deviation) typically indicates */
  signalMeaning: string
  /** Common root causes when this measure signals */
  typicalCauses: string[]
  /** Available analysis types for this measure */
  analysisOptions: MeasureAnalysisOption[]
  /** Related measures that often correlate */
  relatedMeasures: string[]
  /** Industry benchmark context */
  benchmarkContext: string
}

export const MEASURE_CONFIGS: Record<string, MeasureConfig> = {
  // ============================================
  // ON-TIME PERFORMANCE (OTP)
  // ============================================
  otp_mx_ratio: {
    id: 'otp_mx_ratio',
    label: 'OTP MX Ratio',
    unit: '%',
    description: 'Percentage of flights departing on-time that were impacted by maintenance-related delays. This is a key indicator of maintenance efficiency and aircraft reliability.',
    signalMeaning: 'A signal indicates maintenance activities are causing more delays than normal, suggesting potential issues with aircraft reliability, parts availability, or maintenance scheduling.',
    typicalCauses: [
      'Unscheduled maintenance events (MELs, AOG situations)',
      'Parts availability or supply chain delays',
      'Maintenance crew staffing or scheduling issues',
      'Aging fleet requiring more frequent repairs',
      'Weather-related maintenance backlogs',
      'Deferred maintenance items accumulating',
    ],
    analysisOptions: [
      {
        id: 'by_aircraft_type',
        label: 'By Aircraft Type',
        description: 'Compare MX delay rates across different aircraft types to identify fleet-specific issues',
        suggestedQuery: 'Break down OTP MX ratio by aircraft type. Which fleet types have the highest maintenance delay rates?',
      },
      {
        id: 'by_delay_code',
        label: 'By Delay Code',
        description: 'Analyze which maintenance delay codes are most frequent',
        suggestedQuery: 'What are the top maintenance delay codes contributing to OTP degradation? Show frequency and average delay minutes.',
      },
      {
        id: 'by_station',
        label: 'By Station',
        description: 'Compare maintenance performance across different stations',
        suggestedQuery: 'Which stations have the highest MX-related delay rates? Are there patterns by hub vs. outstation?',
      },
      {
        id: 'trend_analysis',
        label: 'Trend Analysis',
        description: 'Examine how MX delays have trended over time',
        suggestedQuery: 'Show the trend of MX delay rates over the past 12 weeks. When did the degradation begin?',
      },
      {
        id: 'mel_impact',
        label: 'MEL Impact',
        description: 'Analyze Minimum Equipment List deferrals and their impact',
        suggestedQuery: 'How many open MEL items exist? What is the correlation between MEL count and delay rates?',
      },
    ],
    relatedMeasures: ['dispatch_reliability', 'aog_rate', 'mtbf', 'mttr', 'parts_availability'],
    benchmarkContext: 'Industry benchmark for MX-related OTP impact is typically 1-3%. Top performers achieve <1%.',
  },

  // ============================================
  // DISPATCH RELIABILITY
  // ============================================
  dispatch_reliability: {
    id: 'dispatch_reliability',
    label: 'Dispatch Reliability',
    unit: '%',
    description: 'Percentage of scheduled flights that depart without mechanical cancellation or delay >15 minutes due to maintenance. This is the primary measure of fleet airworthiness.',
    signalMeaning: 'A signal indicates aircraft are experiencing more mechanical issues than normal, potentially affecting schedule integrity and customer experience.',
    typicalCauses: [
      'Increased component failures or reliability issues',
      'Maintenance program effectiveness declining',
      'Fleet age-related reliability degradation',
      'Inadequate preventive maintenance coverage',
      'Supply chain issues affecting parts availability',
      'Maintenance workforce capacity constraints',
    ],
    analysisOptions: [
      {
        id: 'by_ata_chapter',
        label: 'By ATA Chapter',
        description: 'Identify which aircraft systems are causing the most dispatch issues',
        suggestedQuery: 'Which ATA chapters have the highest dispatch interruption rates? Show top 10 with failure counts.',
      },
      {
        id: 'by_fleet',
        label: 'By Fleet Type',
        description: 'Compare dispatch reliability across different aircraft types',
        suggestedQuery: 'Compare dispatch reliability by fleet type. Which aircraft have the lowest reliability?',
      },
      {
        id: 'repeat_defects',
        label: 'Repeat Defects',
        description: 'Analyze recurring maintenance issues',
        suggestedQuery: 'What percentage of dispatch delays are from repeat defects? Which defects recur most frequently?',
      },
      {
        id: 'time_of_day',
        label: 'Time of Day Pattern',
        description: 'Examine if dispatch issues cluster at certain times',
        suggestedQuery: 'Do dispatch reliability issues cluster at certain times of day? Compare morning vs. evening performance.',
      },
      {
        id: 'weather_correlation',
        label: 'Weather Correlation',
        description: 'Analyze weather impact on mechanical reliability',
        suggestedQuery: 'Is there correlation between weather conditions and dispatch reliability? Compare hot/cold weather periods.',
      },
    ],
    relatedMeasures: ['otp_mx_ratio', 'cancellation_rate', 'aog_rate', 'mtbf'],
    benchmarkContext: 'Industry benchmark is 98-99%. World-class operators achieve >99.5% dispatch reliability.',
  },

  // ============================================
  // CANCELLATION RATE
  // ============================================
  cancellation_rate: {
    id: 'cancellation_rate',
    label: 'Cancellation Rate',
    unit: '%',
    description: 'Percentage of scheduled flights cancelled due to any cause. Cancellations have severe customer impact and operational cost implications.',
    signalMeaning: 'A signal indicates more flights are being cancelled than normal, requiring immediate investigation into root causes.',
    typicalCauses: [
      'Severe weather events',
      'Aircraft mechanical issues (AOG)',
      'Crew availability problems',
      'Air traffic control restrictions',
      'Security or safety incidents',
      'Operational control decisions',
    ],
    analysisOptions: [
      {
        id: 'by_cause_code',
        label: 'By Cause Code',
        description: 'Break down cancellations by root cause category',
        suggestedQuery: 'What are the top cancellation cause codes? Show breakdown by controllable vs. uncontrollable.',
      },
      {
        id: 'by_route',
        label: 'By Route',
        description: 'Identify routes with highest cancellation rates',
        suggestedQuery: 'Which routes have the highest cancellation rates? Are there geographic patterns?',
      },
      {
        id: 'mx_cancellations',
        label: 'MX Cancellations',
        description: 'Focus on maintenance-related cancellations',
        suggestedQuery: 'What percentage of cancellations are maintenance-related? Which aircraft or systems are involved?',
      },
      {
        id: 'crew_cancellations',
        label: 'Crew-Related',
        description: 'Analyze crew availability impact',
        suggestedQuery: 'How many cancellations are due to crew issues? Is this a staffing or scheduling problem?',
      },
      {
        id: 'recovery_analysis',
        label: 'Recovery Analysis',
        description: 'Examine how well operations recovers from disruptions',
        suggestedQuery: 'After a cancellation event, how quickly does the operation recover? What is the cascade effect?',
      },
    ],
    relatedMeasures: ['dispatch_reliability', 'completion_factor', 'misconnect_rate'],
    benchmarkContext: 'Industry average is 1-2% cancellation rate. Best performers achieve <0.5%.',
  },

  // ============================================
  // COMPLETION FACTOR
  // ============================================
  completion_factor: {
    id: 'completion_factor',
    label: 'Completion Factor',
    unit: '%',
    description: 'Percentage of scheduled flights that actually operate. This is the inverse view of cancellations, measuring schedule integrity.',
    signalMeaning: 'A signal indicates schedule integrity is degrading, with more flights not completing as planned.',
    typicalCauses: [
      'Increased cancellation rates',
      'Diversions not returning to schedule',
      'Aircraft swaps reducing capacity',
      'Crew legality issues',
      'Maintenance-driven schedule changes',
    ],
    analysisOptions: [
      {
        id: 'by_day_of_week',
        label: 'By Day of Week',
        description: 'Identify if certain days have lower completion',
        suggestedQuery: 'Does completion factor vary by day of week? Which days have the most schedule disruption?',
      },
      {
        id: 'by_hub',
        label: 'By Hub',
        description: 'Compare completion across hub operations',
        suggestedQuery: 'Compare completion factor across hubs. Which hub has the most schedule integrity issues?',
      },
      {
        id: 'diversion_impact',
        label: 'Diversion Impact',
        description: 'Analyze how diversions affect completion',
        suggestedQuery: 'How do diversions impact completion factor? What percentage of diverted flights miss subsequent legs?',
      },
    ],
    relatedMeasures: ['cancellation_rate', 'dispatch_reliability', 'utilization'],
    benchmarkContext: 'Target completion factor is typically 98-99%.',
  },

  // ============================================
  // AOG (AIRCRAFT ON GROUND) RATE
  // ============================================
  aog_rate: {
    id: 'aog_rate',
    label: 'AOG Rate',
    unit: 'events/day',
    description: 'Rate of Aircraft on Ground events where aircraft cannot fly due to maintenance issues. AOG events are critical operational disruptions.',
    signalMeaning: 'A signal indicates more aircraft are being grounded than normal, suggesting reliability or parts availability issues.',
    typicalCauses: [
      'Critical component failures',
      'Parts not available for repair',
      'Specialized tooling or equipment unavailable',
      'Qualified technician availability',
      'Regulatory compliance issues',
      'Damage events requiring inspection',
    ],
    analysisOptions: [
      {
        id: 'by_component',
        label: 'By Component',
        description: 'Identify which components cause most AOG events',
        suggestedQuery: 'Which components or systems cause the most AOG events? Show top 10 by frequency.',
      },
      {
        id: 'duration_analysis',
        label: 'Duration Analysis',
        description: 'Analyze how long AOG events last',
        suggestedQuery: 'What is the average AOG duration? Which events take longest to resolve?',
      },
      {
        id: 'parts_related',
        label: 'Parts-Related AOG',
        description: 'Focus on AOG events caused by parts unavailability',
        suggestedQuery: 'What percentage of AOG events are due to parts unavailability? Which parts are most problematic?',
      },
      {
        id: 'location_analysis',
        label: 'By Location',
        description: 'Analyze AOG events by station',
        suggestedQuery: 'Where do AOG events occur most frequently? Compare hub vs. outstation AOG rates.',
      },
    ],
    relatedMeasures: ['dispatch_reliability', 'parts_availability', 'mttr', 'spare_ratio'],
    benchmarkContext: 'Target is typically <1 AOG event per 1000 departures.',
  },

  // ============================================
  // MTBF (MEAN TIME BETWEEN FAILURES)
  // ============================================
  mtbf: {
    id: 'mtbf',
    label: 'MTBF',
    unit: 'flight hours',
    description: 'Mean Time Between Failures - average operating time between component or system failures. Higher MTBF indicates better reliability.',
    signalMeaning: 'A declining MTBF signal indicates components are failing more frequently, suggesting reliability degradation.',
    typicalCauses: [
      'Component aging or wear-out',
      'Manufacturing quality issues',
      'Improper maintenance procedures',
      'Environmental stress factors',
      'Design deficiencies',
      'Counterfeit or substandard parts',
    ],
    analysisOptions: [
      {
        id: 'by_component',
        label: 'By Component',
        description: 'Compare MTBF across different components',
        suggestedQuery: 'Which components have the lowest MTBF? Show trend over past 6 months.',
      },
      {
        id: 'by_fleet',
        label: 'By Fleet',
        description: 'Compare reliability across fleet types',
        suggestedQuery: 'Compare MTBF by fleet type. Which aircraft have declining reliability?',
      },
      {
        id: 'vendor_analysis',
        label: 'By Vendor/OEM',
        description: 'Analyze reliability by parts supplier',
        suggestedQuery: 'Is there correlation between parts vendor and MTBF? Which suppliers have reliability issues?',
      },
    ],
    relatedMeasures: ['mttr', 'dispatch_reliability', 'component_removal_rate'],
    benchmarkContext: 'MTBF targets vary by component. Critical systems typically target >10,000 flight hours.',
  },

  // ============================================
  // MTTR (MEAN TIME TO REPAIR)
  // ============================================
  mttr: {
    id: 'mttr',
    label: 'MTTR',
    unit: 'hours',
    description: 'Mean Time To Repair - average time to restore aircraft to service after a failure. Lower MTTR indicates better maintenance efficiency.',
    signalMeaning: 'An increasing MTTR signal indicates repairs are taking longer, suggesting workforce, parts, or process issues.',
    typicalCauses: [
      'Parts availability delays',
      'Technician skill gaps',
      'Complex troubleshooting requirements',
      'Tooling or equipment unavailability',
      'Documentation or procedure issues',
      'Shift handover inefficiencies',
    ],
    analysisOptions: [
      {
        id: 'by_repair_type',
        label: 'By Repair Type',
        description: 'Compare repair times across different maintenance types',
        suggestedQuery: 'Which repair types take longest? Compare scheduled vs. unscheduled maintenance MTTR.',
      },
      {
        id: 'by_station',
        label: 'By Station',
        description: 'Compare repair efficiency across stations',
        suggestedQuery: 'Which stations have the longest MTTR? Are there capability gaps at certain locations?',
      },
      {
        id: 'parts_wait_time',
        label: 'Parts Wait Time',
        description: 'Analyze how much of MTTR is waiting for parts',
        suggestedQuery: 'What percentage of MTTR is parts wait time vs. active repair time?',
      },
    ],
    relatedMeasures: ['mtbf', 'aog_rate', 'parts_availability', 'technician_productivity'],
    benchmarkContext: 'Target MTTR varies by repair type. Line maintenance typically targets <2 hours.',
  },

  // ============================================
  // DELAY MINUTES PER DEPARTURE
  // ============================================
  delay_minutes: {
    id: 'delay_minutes',
    label: 'Delay Minutes',
    unit: 'min/departure',
    description: 'Average delay minutes per departure attributed to maintenance. This measures the severity of delays, not just frequency.',
    signalMeaning: 'A signal indicates maintenance delays are becoming longer on average, suggesting more complex issues or slower resolution.',
    typicalCauses: [
      'Complex mechanical issues requiring extended troubleshooting',
      'Parts not readily available',
      'Insufficient maintenance staffing',
      'Multiple concurrent issues',
      'Deferred items requiring attention',
    ],
    analysisOptions: [
      {
        id: 'by_delay_bucket',
        label: 'By Delay Duration',
        description: 'Categorize delays by duration buckets',
        suggestedQuery: 'Break down delays into buckets: 0-15min, 15-30min, 30-60min, >60min. Which bucket is growing?',
      },
      {
        id: 'by_cause',
        label: 'By Root Cause',
        description: 'Analyze delay minutes by cause category',
        suggestedQuery: 'Which maintenance causes contribute most delay minutes? Show Pareto analysis.',
      },
      {
        id: 'trend',
        label: 'Trend Analysis',
        description: 'Examine delay minute trends over time',
        suggestedQuery: 'How have average delay minutes trended over the past 8 weeks?',
      },
    ],
    relatedMeasures: ['otp_mx_ratio', 'mttr', 'dispatch_reliability'],
    benchmarkContext: 'Industry target is typically <5 delay minutes per departure for MX causes.',
  },

  // ============================================
  // PARTS AVAILABILITY
  // ============================================
  parts_availability: {
    id: 'parts_availability',
    label: 'Parts Availability',
    unit: '%',
    description: 'Percentage of maintenance events where required parts were immediately available. Critical for minimizing aircraft downtime.',
    signalMeaning: 'A signal indicates parts are not available when needed, causing extended aircraft downtime and delays.',
    typicalCauses: [
      'Inventory stocking level issues',
      'Supply chain disruptions',
      'Demand forecasting errors',
      'Vendor delivery delays',
      'Warehouse distribution issues',
      'Unexpected consumption spikes',
    ],
    analysisOptions: [
      {
        id: 'by_part_category',
        label: 'By Part Category',
        description: 'Identify which part categories have availability issues',
        suggestedQuery: 'Which part categories have the lowest availability? Show rotables vs. expendables.',
      },
      {
        id: 'stockout_analysis',
        label: 'Stockout Analysis',
        description: 'Analyze stockout events and their impact',
        suggestedQuery: 'How many stockout events occurred? What was the average delay caused by each stockout?',
      },
      {
        id: 'by_station',
        label: 'By Station',
        description: 'Compare parts availability across stations',
        suggestedQuery: 'Which stations have the worst parts availability? Are outstations adequately stocked?',
      },
    ],
    relatedMeasures: ['aog_rate', 'mttr', 'inventory_turns'],
    benchmarkContext: 'Target parts availability is typically >95% for critical items.',
  },

  // ============================================
  // UTILIZATION
  // ============================================
  utilization: {
    id: 'utilization',
    label: 'Aircraft Utilization',
    unit: 'block hours/day',
    description: 'Average daily block hours per aircraft. Higher utilization means better asset productivity but must balance with maintenance needs.',
    signalMeaning: 'A signal indicates aircraft are flying more or less than planned, affecting revenue and maintenance scheduling.',
    typicalCauses: [
      'Schedule changes or reductions',
      'Increased maintenance downtime',
      'Crew availability constraints',
      'Demand fluctuations',
      'Operational disruptions',
    ],
    analysisOptions: [
      {
        id: 'by_fleet',
        label: 'By Fleet Type',
        description: 'Compare utilization across fleet types',
        suggestedQuery: 'Compare utilization by fleet type. Which aircraft are underutilized?',
      },
      {
        id: 'mx_impact',
        label: 'MX Impact on Utilization',
        description: 'Analyze how maintenance affects utilization',
        suggestedQuery: 'How much utilization is lost to maintenance? Compare scheduled vs. unscheduled MX impact.',
      },
      {
        id: 'trend',
        label: 'Trend Analysis',
        description: 'Examine utilization trends',
        suggestedQuery: 'How has utilization trended over the past quarter? What is driving the change?',
      },
    ],
    relatedMeasures: ['dispatch_reliability', 'completion_factor', 'maintenance_ratio'],
    benchmarkContext: 'Typical narrowbody utilization is 10-12 block hours/day. Widebody is 12-16 hours/day.',
  },
}

/**
 * Get measure config by ID, with fallback for unknown measures
 */
export function getMeasureConfig(measureId: string): MeasureConfig {
  const normalized = measureId.toLowerCase().replace(/[\s-]/g, '_')
  
  // Try exact match first
  if (MEASURE_CONFIGS[normalized]) {
    return MEASURE_CONFIGS[normalized]
  }
  
  // Try partial match
  for (const [key, config] of Object.entries(MEASURE_CONFIGS)) {
    if (normalized.includes(key) || key.includes(normalized)) {
      return config
    }
  }
  
  // Return generic config for unknown measures
  return {
    id: measureId,
    label: measureId.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
    unit: '',
    description: `Analysis of ${measureId} metric performance and trends.`,
    signalMeaning: 'A signal indicates this metric has deviated from normal operating range.',
    typicalCauses: [
      'Process or operational changes',
      'External factors',
      'Data quality issues',
      'Seasonal variations',
    ],
    analysisOptions: [
      {
        id: 'trend',
        label: 'Trend Analysis',
        description: 'Examine how this metric has changed over time',
        suggestedQuery: `Show the trend of ${measureId} over the past 12 weeks. When did the change begin?`,
      },
      {
        id: 'breakdown',
        label: 'Breakdown Analysis',
        description: 'Break down by contributing factors',
        suggestedQuery: `What factors are contributing to the ${measureId} signal? Show breakdown by category.`,
      },
      {
        id: 'correlation',
        label: 'Correlation Analysis',
        description: 'Find correlated metrics',
        suggestedQuery: `Which other metrics correlate with ${measureId}? Are there leading indicators?`,
      },
    ],
    relatedMeasures: [],
    benchmarkContext: 'Benchmark data not available for this measure.',
  }
}

/**
 * Generate a contextual prompt for investigating a specific measure
 */
export function generateInvestigationPrompt(
  measureId: string,
  station: string,
  window: 'weekly' | 'daily',
  pointT?: string
): string {
  const config = getMeasureConfig(measureId)
  const timeContext = pointT 
    ? `around ${pointT}` 
    : `in the ${window} view`
  
  return `Investigate why ${config.label} is signaling at station ${station} ${timeContext}.

**About this measure:** ${config.description}

**What this signal typically means:** ${config.signalMeaning}

**Common root causes to investigate:**
${config.typicalCauses.map(c => `• ${c}`).join('\n')}

Start by identifying the primary driver of this signal, then drill down into specific contributing factors.`
}
