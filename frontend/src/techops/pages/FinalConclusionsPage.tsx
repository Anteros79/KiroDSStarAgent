import { useEffect, useMemo, useState } from 'react'
import { techOpsApi } from '../api'
import { EvidenceItem, FinalizeInvestigationRequest, InvestigationRecord } from '../types'
import { ArrowLeft, CheckCircle2, Loader2, Save, XCircle } from 'lucide-react'
import ChartDisplay from '../../components/ChartDisplay'

function asText(v: unknown) {
  return typeof v === 'string' ? v : v == null ? '' : String(v)
}

export function FinalConclusionsPage({
  investigationId,
  onBack,
  onDone,
}: {
  investigationId: string
  onBack: () => void
  onDone?: () => void
}) {
  const [inv, setInv] = useState<InvestigationRecord | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [rootCause, setRootCause] = useState('')
  const [actions, setActions] = useState<string[]>([])
  const [actionDraft, setActionDraft] = useState('')
  const [notes, setNotes] = useState('')

  const [selected, setSelected] = useState<Record<string, boolean>>({})

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setSuccess(null)
    techOpsApi
      .getInvestigation(investigationId)
      .then((data) => {
        if (cancelled) return
        setInv(data)
        setRootCause(data.final_root_cause || '')
        setActions(data.final_actions || [])
        setNotes(data.final_notes || '')
        setLoading(false)
      })
      .catch((e) => {
        if (cancelled) return
        setError(e instanceof Error ? e.message : 'Failed to load investigation')
        setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [investigationId])

  const evidenceCandidates = useMemo(() => {
    if (!inv) return [] as Array<{ key: string; item: EvidenceItem; preview?: any }>

    const out: Array<{ key: string; item: EvidenceItem; preview?: any }> = []

    if (inv.telemetry) {
      out.push({
        key: `telemetry`,
        item: { kind: 'telemetry', label: inv.telemetry.title, investigation_id: inv.investigation_id, chart: inv.telemetry },
        preview: inv.telemetry,
      })
    }

    for (const d of Array.from(new Map((inv.diagnostics || []).map((x) => [x.name, x])).values())) {
      out.push({
        key: `diag:${d.name}`,
        item: {
          kind: 'diagnostic',
          label: d.name,
          investigation_id: inv.investigation_id,
          excerpt: d.detail,
          meta: { status: d.status, confidence: d.confidence },
        },
      })
    }

    for (const step of (inv.steps || []) as any[]) {
      const stepId = asText(step.step_id)
      const stepNum = asText(step.step_number || '')
      const stepQuery = asText(step.query)
      for (const it of (step.iterations || []) as any[]) {
        const iterId = asText(it.iteration_id)
        const iterNum = asText(it.iteration_number || '')
        const iterQuery = asText(it.query) || stepQuery
        const resp = asText(it.response)
        const chart = it.chart
        out.push({
          key: `iter:${stepId}:${iterId}`,
          item: {
            kind: 'iteration',
            label: `Step ${stepNum} · Iter ${iterNum}`,
            investigation_id: inv.investigation_id,
            step_id: stepId,
            iteration_id: iterId,
            excerpt: resp ? resp.slice(0, 420) : '',
            meta: { query: iterQuery },
            chart,
          },
          preview: chart,
        })
      }
    }

    return out
  }, [inv])

  useEffect(() => {
    // Initialize selection state once we have candidates
    if (!evidenceCandidates.length) return
    setSelected((prev) => {
      // If already initialized (user toggled), don't clobber.
      if (Object.keys(prev).length) return prev
      const next: Record<string, boolean> = {}
      for (const e of evidenceCandidates) next[e.key] = true
      return next
    })
  }, [evidenceCandidates])

  const selectedEvidence = useMemo(() => {
    return evidenceCandidates.filter((e) => selected[e.key]).map((e) => e.item)
  }, [evidenceCandidates, selected])

  const handleSave = async () => {
    if (!inv) return
    setSaving(true)
    setError(null)
    setSuccess(null)
    try {
      const pendingAction = actionDraft.trim()
      const nextActions = pendingAction ? Array.from(new Set([...actions, pendingAction])) : actions

      const payload: FinalizeInvestigationRequest = {
        final_root_cause: rootCause.trim(),
        final_actions: nextActions.filter(Boolean),
        final_notes: notes.trim() || null,
        evidence: selectedEvidence,
      }
      const updated = await techOpsApi.finalizeInvestigation(inv.investigation_id, payload)
      setInv(updated)
      setActions(nextActions)
      setActionDraft('')
      setSuccess('Final conclusions saved.')
      if (onDone) onDone()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to finalize investigation')
    } finally {
      setSaving(false)
    }
  }

  const addAction = () => {
    const v = actionDraft.trim()
    if (!v) return
    setActions((prev) => Array.from(new Set([...prev, v])))
    setActionDraft('')
  }

  return (
    <div className="px-6 py-6">
      <div className="max-w-7xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onBack}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Investigation
            </button>
            <div>
              <div className="text-xs text-slate-500">Operations &gt; Signal Monitor</div>
              <div className="flex items-center gap-3">
                <h2 className="text-2xl font-extrabold text-slate-900">
                  Final Conclusions{inv ? ` · #${inv.investigation_id}` : ''}
                </h2>
              </div>
            </div>
          </div>

          <button
            onClick={handleSave}
            disabled={saving || !rootCause.trim()}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[#0B2A55] hover:bg-[#082043] text-white font-semibold disabled:opacity-50"
            title={!rootCause.trim() ? 'Root cause is required' : 'Save final conclusions'}
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
            Save Final
          </button>
        </div>

        {loading && (
          <div className="bg-white border border-slate-200 rounded-xl p-6 text-slate-600">
            Loading final conclusions…
          </div>
        )}

        {error && (
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-rose-800 flex items-start gap-3">
            <XCircle className="w-5 h-5 mt-0.5" />
            <div>{error}</div>
          </div>
        )}

        {success && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6 text-emerald-800 flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 mt-0.5" />
            <div>{success}</div>
          </div>
        )}

        {!loading && inv && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Evidence / artifacts */}
            <div className="lg:col-span-2 space-y-4">
              <div className="bg-white border border-slate-200 rounded-xl p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-sm font-extrabold text-slate-900">Attach Investigation Artifacts</div>
                    <div className="text-xs text-slate-500 mt-1">
                      Toggle what DS‑STAR evidence will be attached to this final conclusion.
                    </div>
                  </div>
                  <div className="text-xs text-slate-600">
                    Selected: <span className="font-bold">{selectedEvidence.length}</span>
                  </div>
                </div>

                <div className="mt-4 space-y-3">
                  {evidenceCandidates.length === 0 ? (
                    <div className="text-sm text-slate-600">
                      No artifacts yet. Run the DS‑STAR investigation first.
                    </div>
                  ) : (
                    evidenceCandidates.map((e) => (
                      <div key={e.key} className="rounded-xl border border-slate-200 p-4">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <div className="text-xs font-bold text-slate-500">{String(e.item.kind).toUpperCase()}</div>
                            <div className="text-sm font-extrabold text-slate-900">{e.item.label || e.key}</div>
                            {e.item.meta?.query && (
                              <div className="mt-1 text-xs text-slate-600">
                                Query: <span className="font-semibold">{String(e.item.meta.query).slice(0, 180)}</span>
                              </div>
                            )}
                            {e.item.excerpt && <div className="mt-2 text-sm text-slate-700 whitespace-pre-wrap">{e.item.excerpt}</div>}
                          </div>
                          <label className="flex items-center gap-2 text-sm text-slate-700">
                            <input
                              type="checkbox"
                              className="h-4 w-4 rounded border-slate-300"
                              checked={!!selected[e.key]}
                              onChange={(ev) => setSelected((prev) => ({ ...prev, [e.key]: ev.target.checked }))}
                            />
                            Include
                          </label>
                        </div>

                        {e.preview?.plotly_json && (
                          <div className="mt-3">
                            <ChartDisplay chart={e.preview as any} />
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Final entry form */}
            <div className="lg:col-span-1 space-y-4">
              <div className="bg-white border border-slate-200 rounded-xl p-5">
                <div className="text-sm font-extrabold text-slate-900">Final Entry</div>
                <div className="text-xs text-slate-500 mt-1">Root cause + actions taken + notes</div>

                <div className="mt-4 space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-slate-600 mb-1">Assignable Root Cause (required)</label>
                    <select
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white"
                      value={rootCause}
                      onChange={(e) => setRootCause(e.target.value)}
                    >
                      <option value="">Select a root cause…</option>
                      <option value="Parts availability / supply delay">Parts availability / supply delay</option>
                      <option value="Staffing / coverage gap">Staffing / coverage gap</option>
                      <option value="MX process / handoff issue">MX process / handoff issue</option>
                      <option value="Vendor / contract performance">Vendor / contract performance</option>
                      <option value="Training / procedural compliance">Training / procedural compliance</option>
                      <option value="Weather / exogenous constraint">Weather / exogenous constraint</option>
                      <option value="Other (specify in notes)">Other (specify in notes)</option>
                    </select>
                    <p className="text-xs text-slate-500 mt-1">You can refine details in Notes.</p>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-600 mb-1">Actions Taken</label>
                    <div className="flex gap-2">
                      <input
                        className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-sm"
                        value={actionDraft}
                        onChange={(e) => setActionDraft(e.target.value)}
                        placeholder="Add an action (e.g., expedite part, add coverage)…"
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') addAction()
                        }}
                      />
                      <button
                        onClick={addAction}
                        className="px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-sm font-semibold"
                      >
                        Add
                      </button>
                    </div>

                    {actions.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {actions.map((a) => (
                          <button
                            key={a}
                            onClick={() => setActions((prev) => prev.filter((x) => x !== a))}
                            className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-bold border border-slate-200 bg-white text-slate-700 hover:bg-rose-50 hover:text-rose-700"
                            title="Remove action"
                          >
                            {a}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-600 mb-1">Final Notes</label>
                    <textarea
                      className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm h-28 resize-none"
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Write the final conclusion narrative, why this root cause, and what to do next…"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

