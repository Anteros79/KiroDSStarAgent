import { useEffect, useState } from 'react'
import { techOpsApi } from '../api'
import { InvestigationRecord } from '../types'
import { getMeasureConfig } from '../measureConfig'
import { 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Eye, 
  Filter, 
  Search,
  ChevronDown,
  ChevronRight,
  FileText,
  BarChart3,
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
  MessageSquare
} from 'lucide-react'
import { ChartDisplay } from '../../components/content/ChartDisplay'

type ReviewStatus = 'pending' | 'approved' | 'rejected' | 'all'

interface AdminReviewPageProps {
  onSelectInvestigation?: (investigationId: string) => void
}

export function AdminReviewPage({ onSelectInvestigation }: AdminReviewPageProps) {
  const [investigations, setInvestigations] = useState<InvestigationRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filterStatus, setFilterStatus] = useState<ReviewStatus>('pending')
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [reviewingId, setReviewingId] = useState<string | null>(null)
  const [reviewComment, setReviewComment] = useState('')

  useEffect(() => {
    loadInvestigations()
  }, [])

  const loadInvestigations = async () => {
    try {
      setLoading(true)
      // Load all investigations (admin view)
      const data = await techOpsApi.listInvestigations()
      setInvestigations(data)
      setError(null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load investigations')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (investigationId: string) => {
    try {
      // TODO: Call API to approve investigation
      console.log('Approving investigation:', investigationId, 'Comment:', reviewComment)
      // Update local state
      setInvestigations(prev => 
        prev.map(inv => 
          inv.investigation_id === investigationId 
            ? { ...inv, status: 'approved' } 
            : inv
        )
      )
      setReviewingId(null)
      setReviewComment('')
    } catch (e) {
      console.error('Failed to approve:', e)
    }
  }

  const handleReject = async (investigationId: string) => {
    try {
      // TODO: Call API to reject investigation
      console.log('Rejecting investigation:', investigationId, 'Comment:', reviewComment)
      // Update local state
      setInvestigations(prev => 
        prev.map(inv => 
          inv.investigation_id === investigationId 
            ? { ...inv, status: 'rejected' } 
            : inv
        )
      )
      setReviewingId(null)
      setReviewComment('')
    } catch (e) {
      console.error('Failed to reject:', e)
    }
  }

  // Filter investigations
  const filteredInvestigations = investigations.filter(inv => {
    // Status filter
    if (filterStatus !== 'all') {
      const invStatus = inv.status?.toLowerCase() || 'pending'
      if (filterStatus === 'pending' && !['pending', 'submitted', 'in_review'].includes(invStatus)) {
        return false
      }
      if (filterStatus === 'approved' && invStatus !== 'approved') {
        return false
      }
      if (filterStatus === 'rejected' && invStatus !== 'rejected') {
        return false
      }
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      const matchesKpi = inv.kpi_id.toLowerCase().includes(query)
      const matchesStation = inv.station.toLowerCase().includes(query)
      const matchesRootCause = inv.final_root_cause?.toLowerCase().includes(query)
      const matchesId = inv.investigation_id.toLowerCase().includes(query)
      if (!matchesKpi && !matchesStation && !matchesRootCause && !matchesId) {
        return false
      }
    }

    return true
  })

  // Group by status for summary
  const statusCounts = {
    pending: investigations.filter(i => ['pending', 'submitted', 'in_review'].includes(i.status?.toLowerCase() || 'pending')).length,
    approved: investigations.filter(i => i.status?.toLowerCase() === 'approved').length,
    rejected: investigations.filter(i => i.status?.toLowerCase() === 'rejected').length,
  }

  if (loading) {
    return (
      <div className="px-6 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-600">
            Loading investigations for review...
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="px-6 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-8 text-center text-rose-800">
            {error}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="px-6 py-6">
      <div className="max-w-7xl mx-auto space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900">Investigation Review Queue</h1>
            <p className="text-sm text-slate-600 mt-1">
              Review and approve finalized investigations submitted by analysts
            </p>
          </div>
          <button
            onClick={loadInvestigations}
            className="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Refresh
          </button>
        </div>

        {/* Status Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatusCard
            label="Pending Review"
            count={statusCounts.pending}
            icon={Clock}
            color="amber"
            active={filterStatus === 'pending'}
            onClick={() => setFilterStatus('pending')}
          />
          <StatusCard
            label="Approved"
            count={statusCounts.approved}
            icon={CheckCircle2}
            color="green"
            active={filterStatus === 'approved'}
            onClick={() => setFilterStatus('approved')}
          />
          <StatusCard
            label="Rejected"
            count={statusCounts.rejected}
            icon={XCircle}
            color="red"
            active={filterStatus === 'rejected'}
            onClick={() => setFilterStatus('rejected')}
          />
        </div>

        {/* Filters */}
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="flex items-center gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search by KPI, station, root cause, or ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-slate-400" />
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value as ReviewStatus)}
                className="px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending Review</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
          </div>
        </div>

        {/* Investigation List */}
        <div className="space-y-3">
          {filteredInvestigations.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-600">
              No investigations match your filters.
            </div>
          ) : (
            filteredInvestigations.map((inv) => (
              <InvestigationReviewCard
                key={inv.investigation_id}
                investigation={inv}
                isExpanded={expandedId === inv.investigation_id}
                isReviewing={reviewingId === inv.investigation_id}
                reviewComment={reviewingId === inv.investigation_id ? reviewComment : ''}
                onToggleExpand={() => setExpandedId(expandedId === inv.investigation_id ? null : inv.investigation_id)}
                onStartReview={() => {
                  setReviewingId(inv.investigation_id)
                  setReviewComment('')
                }}
                onCancelReview={() => {
                  setReviewingId(null)
                  setReviewComment('')
                }}
                onCommentChange={setReviewComment}
                onApprove={() => handleApprove(inv.investigation_id)}
                onReject={() => handleReject(inv.investigation_id)}
                onViewDetails={() => onSelectInvestigation?.(inv.investigation_id)}
              />
            ))
          )}
        </div>
      </div>
    </div>
  )
}

function StatusCard({
  label,
  count,
  icon: Icon,
  color,
  active,
  onClick,
}: {
  label: string
  count: number
  icon: typeof Clock
  color: 'amber' | 'green' | 'red'
  active: boolean
  onClick: () => void
}) {
  const colorClasses = {
    amber: {
      bg: active ? 'bg-amber-100' : 'bg-amber-50',
      border: active ? 'border-amber-400' : 'border-amber-200',
      icon: 'text-amber-600',
      text: 'text-amber-900',
    },
    green: {
      bg: active ? 'bg-green-100' : 'bg-green-50',
      border: active ? 'border-green-400' : 'border-green-200',
      icon: 'text-green-600',
      text: 'text-green-900',
    },
    red: {
      bg: active ? 'bg-red-100' : 'bg-red-50',
      border: active ? 'border-red-400' : 'border-red-200',
      icon: 'text-red-600',
      text: 'text-red-900',
    },
  }

  const classes = colorClasses[color]

  return (
    <button
      onClick={onClick}
      className={`${classes.bg} border-2 ${classes.border} rounded-xl p-4 text-left transition-all hover:shadow-md`}
    >
      <div className="flex items-center justify-between">
        <Icon className={`w-6 h-6 ${classes.icon}`} />
        <span className={`text-3xl font-extrabold ${classes.text}`}>{count}</span>
      </div>
      <div className={`text-sm font-semibold ${classes.text} mt-2`}>{label}</div>
    </button>
  )
}

function InvestigationReviewCard({
  investigation,
  isExpanded,
  isReviewing,
  reviewComment,
  onToggleExpand,
  onStartReview,
  onCancelReview,
  onCommentChange,
  onApprove,
  onReject,
  onViewDetails,
}: {
  investigation: InvestigationRecord
  isExpanded: boolean
  isReviewing: boolean
  reviewComment: string
  onToggleExpand: () => void
  onStartReview: () => void
  onCancelReview: () => void
  onCommentChange: (comment: string) => void
  onApprove: () => void
  onReject: () => void
  onViewDetails: () => void
}) {
  const measureConfig = getMeasureConfig(investigation.kpi_id)
  const status = investigation.status?.toLowerCase() || 'pending'
  const isPending = ['pending', 'submitted', 'in_review'].includes(status)

  const statusBadge = {
    pending: { bg: 'bg-amber-100', text: 'text-amber-800', label: 'PENDING REVIEW' },
    submitted: { bg: 'bg-amber-100', text: 'text-amber-800', label: 'SUBMITTED' },
    in_review: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'IN REVIEW' },
    approved: { bg: 'bg-green-100', text: 'text-green-800', label: 'APPROVED' },
    rejected: { bg: 'bg-red-100', text: 'text-red-800', label: 'REJECTED' },
  }[status] || { bg: 'bg-slate-100', text: 'text-slate-800', label: status.toUpperCase() }

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
      {/* Header Row */}
      <div
        className="px-4 py-3 flex items-center gap-4 cursor-pointer hover:bg-slate-50 transition-colors"
        onClick={onToggleExpand}
      >
        {isExpanded ? (
          <ChevronDown className="w-5 h-5 text-slate-400 flex-shrink-0" />
        ) : (
          <ChevronRight className="w-5 h-5 text-slate-400 flex-shrink-0" />
        )}

        <div className="flex-1 min-w-0 grid grid-cols-1 md:grid-cols-5 gap-3">
          <div>
            <div className="text-xs text-slate-500 font-semibold">ID</div>
            <div className="text-sm font-bold text-slate-900">#{investigation.investigation_id}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold">KPI</div>
            <div className="text-sm font-bold text-slate-900">{measureConfig.label}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold">STATION</div>
            <div className="text-sm font-bold text-slate-900">{investigation.station}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold">SUBMITTED BY</div>
            <div className="text-sm font-bold text-slate-900">{investigation.created_by?.name || 'Unknown'}</div>
          </div>
          <div>
            <div className="text-xs text-slate-500 font-semibold">DATE</div>
            <div className="text-sm font-bold text-slate-900">
              {new Date(investigation.created_at).toLocaleDateString()}
            </div>
          </div>
        </div>

        <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${statusBadge.bg} ${statusBadge.text}`}>
          {statusBadge.label}
        </span>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-slate-100 bg-slate-50/50">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
            {/* Root Cause */}
            <div className="bg-white rounded-lg border border-slate-200 p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-orange-500" />
                <span className="text-sm font-bold text-slate-900">Root Cause Analysis</span>
              </div>
              <p className="text-sm text-slate-700">
                {investigation.final_root_cause || 'No root cause documented'}
              </p>
            </div>

            {/* Recommended Actions */}
            <div className="bg-white rounded-lg border border-slate-200 p-4">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="w-4 h-4 text-blue-500" />
                <span className="text-sm font-bold text-slate-900">Recommended Actions</span>
              </div>
              {investigation.final_actions && investigation.final_actions.length > 0 ? (
                <ul className="space-y-1">
                  {investigation.final_actions.map((action, i) => (
                    <li key={i} className="text-sm text-slate-700 flex items-start gap-2">
                      <span className="text-blue-400">•</span>
                      {action}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-slate-500">No actions documented</p>
              )}
            </div>

            {/* Evidence */}
            {investigation.final_evidence && investigation.final_evidence.length > 0 && (
              <div className="lg:col-span-2 bg-white rounded-lg border border-slate-200 p-4">
                <div className="flex items-center gap-2 mb-3">
                  <BarChart3 className="w-4 h-4 text-purple-500" />
                  <span className="text-sm font-bold text-slate-900">
                    Supporting Evidence ({investigation.final_evidence.length} items)
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {investigation.final_evidence.slice(0, 4).map((evidence: any, i: number) => (
                    <div key={i} className="bg-slate-50 rounded-lg p-3 border border-slate-200">
                      <div className="text-xs font-bold text-slate-500 uppercase mb-1">
                        {evidence.kind || 'Evidence'}
                      </div>
                      {evidence.chart && (
                        <div className="mt-2">
                          <ChartDisplay chart={evidence.chart} />
                        </div>
                      )}
                      {evidence.excerpt && (
                        <p className="text-sm text-slate-700 mt-1">{evidence.excerpt}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Notes */}
            {investigation.final_notes && (
              <div className="lg:col-span-2 bg-white rounded-lg border border-slate-200 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <MessageSquare className="w-4 h-4 text-slate-500" />
                  <span className="text-sm font-bold text-slate-900">Analyst Notes</span>
                </div>
                <p className="text-sm text-slate-700 whitespace-pre-wrap">{investigation.final_notes}</p>
              </div>
            )}
          </div>

          {/* Review Actions */}
          {isPending && (
            <div className="mt-4 pt-4 border-t border-slate-200">
              {isReviewing ? (
                <div className="space-y-3">
                  <textarea
                    value={reviewComment}
                    onChange={(e) => onCommentChange(e.target.value)}
                    placeholder="Add review comments (optional)..."
                    className="w-full h-20 p-3 border border-slate-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <div className="flex items-center gap-3">
                    <button
                      onClick={onApprove}
                      className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg transition-colors"
                    >
                      <ThumbsUp className="w-4 h-4" />
                      Approve Investigation
                    </button>
                    <button
                      onClick={onReject}
                      className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg transition-colors"
                    >
                      <ThumbsDown className="w-4 h-4" />
                      Reject & Return
                    </button>
                    <button
                      onClick={onCancelReview}
                      className="px-4 py-2 border border-slate-200 text-slate-700 font-medium rounded-lg hover:bg-slate-50 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <button
                    onClick={onStartReview}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors"
                  >
                    <Eye className="w-4 h-4" />
                    Start Review
                  </button>
                  <button
                    onClick={onViewDetails}
                    className="flex items-center gap-2 px-4 py-2 border border-slate-200 text-slate-700 font-medium rounded-lg hover:bg-slate-50 transition-colors"
                  >
                    <FileText className="w-4 h-4" />
                    View Full Details
                  </button>
                </div>
              )}
            </div>
          )}

          {!isPending && (
            <div className="mt-4 pt-4 border-t border-slate-200">
              <button
                onClick={onViewDetails}
                className="flex items-center gap-2 px-4 py-2 border border-slate-200 text-slate-700 font-medium rounded-lg hover:bg-slate-50 transition-colors"
              >
                <FileText className="w-4 h-4" />
                View Full Details
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
