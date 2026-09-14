import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { reportsApi } from '../../services/api';
import { Report } from '../../types';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { ErrorState } from '../../components/ui/ErrorState';
import { formatDistanceToNow } from 'date-fns';
import { ShieldAlert, CheckCircle, Clock, AlertTriangle, Eye } from 'lucide-react';
import { cn } from '../../lib/utils';

export default function AdminDashboard() {
  const [searchParams] = useSearchParams();
  const statusFilter = searchParams.get('status') || 'All';
  
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReports = async () => {
    try {
      setLoading(true);
      const res = await reportsApi.getReports(statusFilter !== 'All' ? { status: statusFilter } : {});
      setReports(res.data.items);
    } catch (err) {
      setError('Failed to fetch reports queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [statusFilter]);

  if (error) return <ErrorState message={error} onRetry={fetchReports} />;

  return (
    <div className="max-w-6xl mx-auto pb-10">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#F4F6F6]">Incident Reports Queue</h1>
        <p className="text-sm text-[#34C759]/70 mt-1">Review, verify, or reject incoming reports</p>
      </div>

      <div className="bg-[#24313D] rounded-xl shadow-sm border border-[#34C759]/20 overflow-hidden">
        <div className="flex border-b border-[#34C759]/20">
          {['All', 'Pending', 'Verified', 'Rejected'].map((tab) => (
            <Link
              key={tab}
              to={tab === 'All' ? '/admin' : `/admin/reports?status=${tab}`}
              className={cn(
                "px-6 py-3 text-sm font-medium border-b-2 transition-colors",
                statusFilter === tab 
                  ? "border-[#34C759]/40 text-[#34C759]/90" 
                  : "border-transparent text-[#34C759]/70 hover:text-[#F4F6F6] hover:border-[#34C759]/40"
              )}
            >
              {tab}
            </Link>
          ))}
        </div>

        <div className="overflow-x-auto relative min-h-[300px]">
          {loading && (
            <div className="absolute inset-0 bg-[#24313D]/50 backdrop-blur-sm z-10 flex items-center justify-center">
              <LoadingSpinner message="Loading queue..." />
            </div>
          )}
          <table className="w-full text-left text-sm text-[#34C759]/70">
            <thead className="bg-[#24313D] text-xs uppercase text-[#34C759]/90 border-b border-[#34C759]/20">
              <tr>
                <th className="px-6 py-4 font-medium">Event Type</th>
                <th className="px-6 py-4 font-medium">Location</th>
                <th className="px-6 py-4 font-medium">Status & Score</th>
                <th className="px-6 py-4 font-medium">AI Flag</th>
                <th className="px-6 py-4 font-medium">Time</th>
                <th className="px-6 py-4 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {reports.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-[#34C759]">
                    No reports found for this filter.
                  </td>
                </tr>
              ) : (
                reports.map((report) => (
                  <tr key={report.id} className="hover:bg-[#24313D] transition-colors">
                    <td className="px-6 py-4 font-medium text-[#F4F6F6]">
                      {report.event_type}
                      <span className="block text-xs font-normal text-[#34C759] mt-1">{report.severity} Severity</span>
                    </td>
                    <td className="px-6 py-4">
                      {report.location.city || 'Unknown City'}
                      <span className="block text-xs text-[#34C759] mt-1">{report.location.lat.toFixed(2)}, {report.location.lng.toFixed(2)}</span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 mb-1">
                        {report.status === 'Verified' && <CheckCircle className="h-4 w-4 text-[#34C759]/90" />}
                        {report.status === 'Pending' && <Clock className="h-4 w-4 text-yellow-400" />}
                        {report.status === 'Rejected' && <AlertTriangle className="h-4 w-4 text-red-400" />}
                        <span className="font-medium text-[#34C759]/90">{report.status}</span>
                      </div>
                      <span className="text-xs text-[#34C759]">Trust: {Math.round(report.trust_score * 100)}</span>
                    </td>
                    <td className="px-6 py-4">
                      {report.ai_verification_info?.is_suspicious ? (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-900/30 text-red-400 rounded text-xs font-medium border border-red-900/50">
                          <ShieldAlert className="h-3 w-3" /> Suspicious
                        </span>
                      ) : (
                        <span className="text-xs text-[#34C759]">Normal</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-[#34C759]">
                      {formatDistanceToNow(new Date(report.created_at))} ago
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link 
                        to={`/admin/reports/${report.id}`}
                        className="inline-flex items-center gap-1 px-3 py-1.5 bg-[#24313D] border border-[#34C759]/40 text-[#F4F6F6] rounded-md text-xs font-medium hover:bg-gray-700 transition-colors shadow-sm"
                      >
                        <Eye className="h-3 w-3" /> Review
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
