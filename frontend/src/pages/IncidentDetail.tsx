import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { eventsApi, reportsApi } from '../services/api';
import { IncidentEvent, Report } from '../types';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { ErrorState } from '../components/ui/ErrorState';
import { MapPin, AlertTriangle, ShieldCheck, Clock, ArrowLeft } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export default function IncidentDetail() {
  const { id } = useParams<{ id: string }>();
  const [event, setEvent] = useState<IncidentEvent | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    if (!id) return;
    try {
      setLoading(true);
      setError(null);
      const eventRes = await eventsApi.getEventById(id);
      setEvent(eventRes.data);
      const reportsRes = await reportsApi.getReports({});
      setReports(reportsRes.data.items.filter(r => r.event_id === id));
    } catch (err) {
      setError('Failed to load incident details.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  if (loading) return <LoadingSpinner message="Loading incident details..." />;
  if (error || !event) return <ErrorState message={error || 'Event not found'} onRetry={fetchData} />;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link to="/" className="inline-flex items-center gap-2 text-sm text-[#34C759]/70 hover:text-[#F4F6F6] mb-6">
        <ArrowLeft className="h-4 w-4" /> Back to Dashboard
      </Link>

      <div className="bg-[#24313D] rounded-xl shadow-sm border border-[#34C759]/20 overflow-hidden mb-8">
        <div className="p-6 md:p-8 border-b border-[#34C759]/20">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-900/30 text-red-400 border border-red-900/50">
                  {event.severity} Severity
                </span>
                <span className="text-sm text-[#34C759]/70 font-medium">Confidence: {Math.round(event.confidence * 100)}%</span>
              </div>
              <h1 className="text-3xl font-bold text-[#F4F6F6] mb-2">{event.event_type} Incident</h1>
              <div className="flex items-center gap-2 text-[#34C759]/70">
                <MapPin className="h-4 w-4" />
                <span>{event.location.city}, {event.location.state} ({event.location.lat}, {event.location.lng})</span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-[#34C759]">Status</p>
              <p className="text-lg font-bold text-[#34C759]/90 uppercase tracking-wide">{event.status}</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 divide-y md:divide-y-0 md:divide-x divide-gray-800 bg-[#1C2833]/80">
          <div className="p-6 text-center">
            <p className="text-2xl font-bold text-[#F4F6F6]">{event.report_counts.total}</p>
            <p className="text-sm font-medium text-[#34C759] mt-1">Total Reports</p>
          </div>
          <div className="p-6 text-center">
            <p className="text-2xl font-bold text-[#34C759]/90">{event.report_counts.verified}</p>
            <p className="text-sm font-medium text-[#34C759] mt-1">Verified</p>
          </div>
          <div className="p-6 text-center">
            <p className="text-2xl font-bold text-yellow-400">{event.report_counts.suspicious}</p>
            <p className="text-sm font-medium text-[#34C759] mt-1">Suspicious</p>
          </div>
          <div className="p-6 text-center">
            <p className="text-2xl font-bold text-[#34C759]/70">{event.report_counts.duplicate}</p>
            <p className="text-sm font-medium text-[#34C759] mt-1">Duplicates</p>
          </div>
        </div>
      </div>

      <h2 className="text-xl font-bold text-[#F4F6F6] mb-4">Related Reports</h2>
      <div className="space-y-4">
        {reports.length === 0 ? (
          <div className="text-center p-8 bg-[#24313D] rounded-xl border border-[#34C759]/20 text-[#34C759]">
            No related reports found.
          </div>
        ) : (
          reports.map((report) => (
            <div key={report.id} className="bg-[#24313D] p-5 rounded-xl border border-[#34C759]/20 shadow-sm flex flex-col md:flex-row gap-4">
              {report.media_urls.length > 0 && (
                <div className="w-full md:w-48 h-32 flex-shrink-0 bg-[#24313D] rounded-lg overflow-hidden">
                  <img src={report.media_urls[0]} alt="Report media" className="w-full h-full object-cover" />
                </div>
              )}
              <div className="flex-1">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    {report.status === 'Verified' ? (
                      <ShieldCheck className="h-5 w-5 text-[#34C759]/90" />
                    ) : report.status === 'Pending' ? (
                      <Clock className="h-5 w-5 text-yellow-400" />
                    ) : (
                      <AlertTriangle className="h-5 w-5 text-red-400" />
                    )}
                    <span className="font-semibold text-[#F4F6F6]">{report.status} Report</span>
                  </div>
                  <span className="text-xs text-[#34C759]/70 font-medium bg-[#24313D] px-2 py-1 rounded">
                    Score: {Math.round(report.trust_score * 100)}
                  </span>
                </div>
                <p className="text-[#34C759]/90 text-sm mb-3">{report.description}</p>
                <div className="flex flex-wrap items-center gap-4 text-xs text-[#34C759]">
                  <span className="flex items-center gap-1">
                    <MapPin className="h-3.5 w-3.5" />
                    {report.location.lat.toFixed(4)}, {report.location.lng.toFixed(4)}
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    {formatDistanceToNow(new Date(report.created_at))} ago
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
