import React, { useEffect, useMemo, useState, useRef } from 'react';
import { analyticsApi, eventsApi } from '../services/api';
import { wsService } from '../services/ws';
import { AnalyticsData, DashboardFilters, IncidentEvent, getVerificationStatus } from '../types';
import { IncidentMap } from '../maps/IncidentMap';
import { FilterBar } from '../components/dashboard/FilterBar';
import { DashboardSkeleton } from '../components/dashboard/DashboardSkeleton';
import { ErrorState } from '../components/ui/ErrorState';
import { BarChart, Bar, Rectangle, XAxis, YAxis, Tooltip, ResponsiveContainer, ComposedChart, Line, CartesianGrid, LineChart, Area } from 'recharts';
import { Activity, ShieldAlert, FileWarning } from 'lucide-react';
import { RangeSelect, ChartRange, rangeToDays } from '../components/dashboard/RangeSelect';
import { getEventColor } from '../lib/eventColors';

export default function PublicDashboard() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [events, setEvents] = useState<IncidentEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<DashboardFilters>({
    dateFrom: null,
    dateTo: null,
    eventType: 'All',
    state: 'All',
    verificationStatus: 'All',
  });
  const [chartRange, setChartRange] = useState<ChartRange>('7d');
  const isMounted = useRef(false);
  const filteredEvents = useMemo(() => {
    return events.filter((e) => {
      if (filters.eventType !== 'All' && e.event_type !== filters.eventType) return false;
      if (filters.state !== 'All' && e.location.state !== filters.state) return false;
      if (filters.verificationStatus !== 'All' && getVerificationStatus(e) !== filters.verificationStatus) return false;
      if (filters.dateFrom && new Date(e.created_at) < new Date(filters.dateFrom)) return false;
      if (filters.dateTo && new Date(e.created_at) > new Date(filters.dateTo + 'T23:59:59')) return false;
      return true;
    });
  }, [events, filters]);

  const filteredEventCountsData = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const e of filteredEvents) counts[e.event_type] = (counts[e.event_type] || 0) + 1;
    return Object.entries(counts).map(([name, count]) => ({ name, count }));
  }, [filteredEvents]);
  const fetchData = async (isInitialLoad = false) => {
    try {
      if (isInitialLoad) setLoading(true);
      else setRefreshing(true);
      setError(null);
      const [analyticsRes, eventsRes] = await Promise.all([
        analyticsApi.getAnalytics(rangeToDays(chartRange)),
        eventsApi.getEvents()
      ]);
      setAnalytics(analyticsRes.data);
      setEvents(eventsRes.data.items);
    } catch (err) {
      // Don't blank the dashboard on a failed background refresh - only
      // surface the error screen if we have no data to show at all.
      if (isInitialLoad || !analytics) setError('Failed to load dashboard data.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const chartEventCounts = useMemo(() => {
    const days = rangeToDays(chartRange);
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);
    const inRange = events.filter((e) => new Date(e.created_at) >= cutoff);
    const counts: Record<string, number> = {};
    for (const e of inRange) counts[e.event_type] = (counts[e.event_type] || 0) + 1;
    return Object.entries(counts).map(([name, count]) => ({ name, count }));
  }, [events, chartRange]);

  useEffect(() => {
    if (!isMounted.current) {
      isMounted.current = true;
      return;
    }
    analyticsApi.getAnalytics(rangeToDays(chartRange))
      .then((res) => setAnalytics(res.data))
      .catch(() => { }); // keep showing the last good data if this fails
  }, [chartRange]);

  useEffect(() => {
    fetchData(true);

    wsService.connect();
    const unsubscribe = wsService.subscribe((event) => {
      if (event.type === 'INCIDENT_UPDATED' || event.type === 'NEW_INCIDENT') {
        setEvents(prev => {
          const exists = prev.find(e => e.id === event.payload.id);
          if (exists) {
            return prev.map(e => e.id === event.payload.id ? event.payload : e);
          }
          return [event.payload, ...prev];
        });
      }
    });

    return () => {
      unsubscribe();
      wsService.disconnect();
    };
  }, []);

  if (loading) return <DashboardSkeleton />;
  if (error || !analytics) return <ErrorState message={error || 'Unknown error'} onRetry={fetchData} />;

  const eventCountsData = Object.entries(analytics.event_counts).map(([name, count]) => ({ name, count }));
  const tooltipStyle = { backgroundColor: '#1C2833', border: '1px solid rgba(223,175,52,0.3)', color: '#F4F6F6', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.5)' };
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header & Filters */}
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#F4F6F6]">National Incident Overview</h1>
          <p className="text-sm text-[#AAB7B8] mt-1">Real-time monitoring of weather events across India</p>
        </div>
        <button
          onClick={() => fetchData(false)}
          disabled={refreshing}
          className="px-4 py-2 bg-[#24313D] border border-[#34C759]/20 text-[#F4F6F6] rounded-md text-sm font-medium hover:bg-[#34C759]/10 shadow-sm transition-colors disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2 self-start sm:self-auto"
        >
          {refreshing && (
            <span className="h-3.5 w-3.5 border-2 border-[#F4F6F6]/40 border-t-[#F4F6F6] rounded-full animate-spin" />
          )}
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {/* Filters */}
      <div className="mb-8">
        <FilterBar events={events} filters={filters} onChange={setFilters} resultCount={filteredEvents.length} />
      </div>

      {/* KPI Cards */}

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div className="glass-card rounded-xl border-l-4 border-l-[#34C759] p-5 flex items-center gap-4">
          <div className="p-3 rounded-lg bg-[#409E99]/15 text-[#409E99] shrink-0">
            <Activity className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm text-[#34C759]/80">Active events</p>
            <p className="text-3xl font-bold text-[#F4F6F6] mt-0.5 tabular-nums">{analytics.kpis.active_events}</p>
          </div>
        </div>
        <div className="glass-card rounded-xl border-l-4 border-l-[#34C759] p-5 flex items-center gap-4">
          <div className="p-3 rounded-lg bg-[#34C759]/15 text-[#34C759] shrink-0">
            <ShieldAlert className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm text-[#34C759]/80">Verified reports</p>
            <p className="text-3xl font-bold text-[#F4F6F6] mt-0.5 tabular-nums">{analytics.kpis.verified_reports}</p>
          </div>
        </div>
        <div className="glass-card rounded-xl border-l-4 border-l-[#F5A623] p-5 flex items-center gap-4">
          <div className="p-3 rounded-lg bg-[#F5A623]/15 text-[#F5A623] shrink-0">
            <FileWarning className="h-6 w-6" />
          </div>
          <div>
            <p className="text-sm text-[#34C759]/80">Suspicious reports</p>
            <p className="text-3xl font-bold text-[#F4F6F6] mt-0.5 tabular-nums">{analytics.kpis.suspicious_reports}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Map Section */}
        <div className="lg:col-span-2 glass-card rounded-xl shadow-sm border border-[#409E99]/20 overflow-hidden flex flex-col min-h-[400px]">
          <div className="p-4  glass-card  bg-[#24313D] flex justify-between items-center">
            <h2 className="font-semibold text-[#F4F6F6]">Live Incident Map</h2>
          </div>
          <div className="flex-1 relative z-0">
            <IncidentMap events={filteredEvents} />
            {filteredEvents.length === 0 && (
              <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-[#24313D]/85 backdrop-blur-sm text-center px-6 rounded-xl">
                {events.length === 0 ? (
                  <>
                    <p className="text-[#F4F6F6] font-medium mb-1">No incidents reported yet</p>
                    <p className="text-sm text-[#34C759]/70">New reports will appear here as they come in.</p>
                  </>
                ) : (
                  <>
                    <p className="text-[#F4F6F6] font-medium mb-1">No incidents match these filters</p>
                    <p className="text-sm text-[#34C759]/70 mb-4">Try widening the date range or clearing a filter.</p>
                  </>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Charts Section */}
        <div className="flex flex-col gap-8">
          <div className="glass-card rounded-xl shadow-sm border border-[#409E99]/20 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-[#F4F6F6]">Event distribution</h2>
              <RangeSelect value={chartRange} onChange={setChartRange} />
            </div>
            <div className="h-[200px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={filteredEventCountsData} layout="vertical" margin={{ top: 0, right: 0, left: 30, bottom: 0 }}>
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} fontSize={12} width={80} tick={{ fill: '#34C759', fillOpacity: 0.8 }} />
                  <Tooltip cursor={{ fill: '#374151' }} contentStyle={tooltipStyle} />
                  <Bar
                    dataKey="count"
                    radius={[0, 4, 4, 0]}
                    barSize={20}
                    shape={(props: any) => (
                      <Rectangle {...props} fill={getEventColor(props.payload?.name)} />
                    )}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="glass-card rounded-xl shadow-sm border border-[#409E99]/20 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-[#F4F6F6]">Incident trend</h2>
              <RangeSelect value={chartRange} onChange={setChartRange} />
            </div>
            <div className="h-[200px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                                <ComposedChart data={analytics.trend} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#409E99" stopOpacity={0.35} />
                      <stop offset="95%" stopColor="#409E99" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(223,175,52,0.15)" />
                  <XAxis dataKey="date" axisLine={false} tickLine={false} fontSize={12} dy={10} tick={{ fill: '#34C759', fillOpacity: 0.8 }} />
                  <YAxis axisLine={false} tickLine={false} fontSize={12} tick={{ fill: '#34C759', fillOpacity: 0.8 }} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Area type="monotone" dataKey="count" stroke="none" fill="url(#trendGradient)" />
                  <Line type="monotone" dataKey="count" stroke="#409E99" strokeWidth={3} dot={{ r: 4, strokeWidth: 2, fill: '#24313D' }} activeDot={{ r: 6 }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
