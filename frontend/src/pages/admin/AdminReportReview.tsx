import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { reportsApi } from '../../services/api';
import { Report } from '../../types';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { ErrorState } from '../../components/ui/ErrorState';
import { ArrowLeft, Check, X, ShieldAlert, AlertTriangle, MapPin, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export default function AdminReportReview() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [pendingAction, setPendingAction] = useState<'reject' | 'escalate' | null>(null);
  const [reasonInput, setReasonInput] = useState('');
  const [reasonError, setReasonError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const fetchReport = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const res = await reportsApi.getReportById(id);
      setReport(res.data);
    } catch (err) {
      setError('Report not found');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReport();
  }, [id]);

  const openReasonModal = (action: 'reject' | 'escalate') => {
    setActionError(null);
    setReasonInput('');
    setReasonError(null);
    setPendingAction(action);
  };

  const closeReasonModal = () => {
    setPendingAction(null);
    setReasonInput('');
    setReasonError(null);
  };

  const runAction = async (action: 'verify' | 'reject' | 'escalate', reason?: string) => {
    if (!id) return;
    try {
      setActionLoading(true);
      setActionError(null);
      await reportsApi.adminAction(id, action, reason);
      navigate('/admin');
    } catch (err) {
      setActionError('Failed to perform action. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleVerify = () => runAction('verify');

  const handleConfirmReason = () => {
    if (!pendingAction) return;
    const trimmed = reasonInput.trim();
    if (trimmed.length < 3) {
      setReasonError('Please enter a reason of at least 3 characters.');
      return;
    }
    const action = pendingAction;
    setPendingAction(null);
    runAction(action, trimmed);
  };
  if (loading) return <LoadingSpinner message="Loading report..." />;
  if (error || !report) return <ErrorState message={error || 'Unknown error'} />;

  return (
    <div className="max-w-4xl mx-auto pb-10">
      <Link to="/admin" className="inline-flex items-center gap-2 text-sm text-[#34C759]/70 hover:text-[#F4F6F6] mb-6">
        <ArrowLeft className="h-4 w-4" /> Back to Queue
      </Link>

      <div className="bg-[#24313D] rounded-xl shadow-sm border border-[#34C759]/20 overflow-hidden">
        <div className="p-6 border-b border-[#34C759]/20 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-xl font-bold text-[#F4F6F6]">Review Report #{report.id.substring(0, 8)}</h1>
            <div className="flex items-center gap-4 mt-2 text-sm text-[#34C759]/70">
              <span className="flex items-center gap-1"><Clock className="h-4 w-4" /> {formatDistanceToNow(new Date(report.created_at))} ago</span>
              <span className="flex items-center gap-1"><MapPin className="h-4 w-4" /> {report.location.city}</span>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => openReasonModal('reject')}
              disabled={actionLoading}
              className="inline-flex items-center gap-2 px-4 py-2 bg-[#34C759] border border-red-900/50 text-red-400 rounded-md text-sm font-medium hover:bg-[#24313D] transition-colors shadow-sm disabled:opacity-50"
            >
              <X className="h-4 w-4" /> Reject
            </button>
            <button
              onClick={handleVerify}
              disabled={actionLoading}
              className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 text-[#F4F6F6] rounded-md text-sm font-medium hover:bg-green-700 transition-colors shadow-sm disabled:opacity-50"
            >
              <Check className="h-4 w-4" /> Verify & Publish
            </button>
          </div>
        </div>
        {actionError && (
          <div className="mx-6 mt-4 p-3 bg-red-900/30 text-red-400 border border-red-900/50 rounded-md text-sm">
            {actionError}
          </div>
        )}
        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-medium text-[#34C759] uppercase tracking-wider mb-2">Details</h3>
              <div className="bg-[#24313D] rounded-lg p-4 space-y-4">
                <div className="flex justify-between">
                  <span className="text-[#34C759]/70 text-sm">Event Type</span>
                  <span className="font-medium text-[#F4F6F6]">{report.event_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#34C759]/70 text-sm">Severity</span>
                  <span className="font-medium text-[#F4F6F6]">{report.severity}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#34C759]/70 text-sm">Status</span>
                  <span className="font-medium text-[#F4F6F6]">{report.status}</span>
                </div>
                <div>
                  <span className="text-[#34C759]/70 text-sm block mb-1">Description</span>
                  <p className="text-[#34C759]/90 text-sm bg-[#24313D] p-3 rounded border border-[#34C759]/20">{report.description}</p>
                </div>
              </div>
            </div>

            {report.ai_verification_info && (
              <div>
                <h3 className="text-sm font-medium text-[#34C759] uppercase tracking-wider mb-2 flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4" /> AI Analysis
                </h3>
                <div className="bg-[#34C759]/20 rounded-lg p-4 border border-[#34C759]/10">
                  <div className="mb-3 flex justify-between items-center">
                    <span className="text-sm font-medium text-[#34C759]/90">Confidence Score</span>
                    <span className="text-lg font-bold text-[#34C759]/90">{Math.round(report.ai_verification_info.confidence * 100)}%</span>
                  </div>
                  {report.ai_verification_info.is_suspicious && (
                    <div className="mb-3 flex items-center gap-2 text-sm text-red-400 font-medium bg-red-900/30 p-2 rounded border border-red-900/50">
                      <AlertTriangle className="h-4 w-4" /> Flagged as potentially suspicious
                    </div>
                  )}
                  <ul className="space-y-2 text-sm text-blue-300">
                    {report.ai_verification_info.reasons.map((r, i) => (
                      <li key={i} className="flex gap-2">
                        <span className="opacity-50">•</span> {r}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>

          <div>
            <h3 className="text-sm font-medium text-[#34C759] uppercase tracking-wider mb-2">Media Evidence</h3>
            {report.media_urls.length > 0 ? (
              <div className="space-y-4">
                {report.media_urls.map((url, i) => (
                  <div key={i} className="rounded-lg overflow-hidden border border-[#34C759]/20 shadow-sm">
                    <img src={url} alt="Evidence" className="w-full h-auto object-cover" />
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-[#24313D] rounded-lg p-8 text-center text-[#34C759] border border-[#34C759]/40 border-dashed">
                No media provided
              </div>
            )}
          </div>
        </div>
      </div>
      {pendingAction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <div className="bg-[#24313D] border border-[#34C759]/30 rounded-xl shadow-lg w-full max-w-md p-6">
            <h2 className="text-lg font-semibold text-[#F4F6F6] mb-1">
              {pendingAction === 'reject' ? 'Reject this report' : 'Escalate this report'}
            </h2>
            <p className="text-sm text-[#34C759]/70 mb-4">
              Please provide a reason for {pendingAction === 'reject' ? 'rejecting' : 'escalating'} this report.
            </p>
            <textarea
              autoFocus
              rows={3}
              value={reasonInput}
              onChange={(e) => { setReasonInput(e.target.value); if (reasonError) setReasonError(null); }}
              placeholder="Enter reason..."
              className="w-full px-4 py-2 bg-[#1C2833] border border-[#34C759]/40 text-[#F4F6F6] rounded-md focus:ring-[#34C759] focus:border-[#34C759]/40 resize-none text-sm"
            />
            {reasonError && (
              <p className="mt-2 text-sm text-red-400">{reasonError}</p>
            )}
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={closeReasonModal}
                className="px-4 py-2 rounded-md text-sm font-medium text-[#34C759] border border-[#34C759]/40 hover:bg-[#34C759]/10 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmReason}
                disabled={actionLoading}
                className="px-4 py-2 rounded-md text-sm font-medium bg-[#34C759] text-[#1C2833] hover:bg-[#E8C15A] transition-colors disabled:opacity-50"
              >
                {actionLoading ? 'Submitting...' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
