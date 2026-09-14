import React from 'react';
import { Calendar, Filter, MapPin, ShieldCheck, X } from 'lucide-react';
import { DashboardFilters, IncidentEvent } from '../../types';

const inputClass =
  'pl-9 pr-8 py-2 bg-[#24313D] border border-[#34C759]/20 text-[#F4F6F6] rounded-md text-sm ' +
  'focus:ring-[#34C759] focus:border-[#34C759]/40 appearance-none shadow-sm w-full';

interface FilterBarProps {
  events: IncidentEvent[];
  filters: DashboardFilters;
  onChange: (filters: DashboardFilters) => void;
  resultCount: number;
}

export function FilterBar({ events, filters, onChange, resultCount }: FilterBarProps) {
  const eventTypes = Array.from(new Set(events.map((e) => e.event_type))).sort();
  const states = Array.from(
    new Set(events.map((e) => e.location.state).filter((s): s is string => !!s))
  ).sort();

  const update = (patch: Partial<DashboardFilters>) => onChange({ ...filters, ...patch });

  const clearAll = () =>
    onChange({ dateFrom: null, dateTo: null, eventType: 'All', state: 'All', verificationStatus: 'All' });

  const hasActiveFilters =
    filters.dateFrom || filters.dateTo || filters.eventType !== 'All' ||
    filters.state !== 'All' || filters.verificationStatus !== 'All';

  return (
    <div className="glass-card rounded-xl px-4 py-3 flex flex-wrap items-center gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <label className="text-xs text-[#AAB7B8] pl-1">From</label>
        <div className="relative">
          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#34C759] pointer-events-none" />
          <input
            type="date"
            className={inputClass + ' focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#34C759]'}
            value={filters.dateFrom ?? ''}
            onChange={(e) => update({ dateFrom: e.target.value || null })}
            aria-label="From date"
          />
        </div>
        <label className="text-xs text-[#AAB7B8] pl-1">To</label>
        <div className="relative">
          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#34C759] pointer-events-none" />
          <input
            type="date"
            className={inputClass + ' focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#34C759]'}
            value={filters.dateTo ?? ''}
            onChange={(e) => update({ dateTo: e.target.value || null })}
            aria-label="To date"
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#34C759] pointer-events-none" />
          <select
            className={inputClass + ' focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#34C759]'}
            value={filters.eventType}
            onChange={(e) => update({ eventType: e.target.value })}
            aria-label="Event type"
          >
            <option value="All">All Events</option>
            {eventTypes.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
        <div className="relative">
          <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#34C759] pointer-events-none" />
          <select
            className={inputClass + ' focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#34C759]'}
            value={filters.state}
            onChange={(e) => update({ state: e.target.value })}
            aria-label="State"
          >
            <option value="All">All States</option>
            {states.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <div className="relative">
          <ShieldCheck className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#34C759] pointer-events-none" />
          <select
            className={inputClass + ' focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#34C759]'}
            value={filters.verificationStatus}
            onChange={(e) => update({ verificationStatus: e.target.value as DashboardFilters['verificationStatus'] })}
            aria-label="Verification status"
          >
            <option value="All">All Statuses</option>
            <option value="Verified">Verified</option>
            <option value="Needs Review">Needs Review</option>
            <option value="Suspicious">Suspicious</option>
            <option value="Unverified">Unverified</option>
          </select>
        </div>
      </div>

      <div className="flex items-center gap-3 ml-auto">
        <span className="text-xs text-[#AAB7B8] whitespace-nowrap">
          {resultCount} {resultCount === 1 ? 'incident' : 'incidents'}
        </span>
        {hasActiveFilters && (
          <button
            onClick={clearAll}
            className="flex items-center gap-1 px-3 py-2 text-sm text-[#34C759] hover:text-[#F4F6F6] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#34C759] rounded whitespace-nowrap"
          >
            <X className="h-3.5 w-3.5" /> Clear
          </button>
        )}
      </div>
    </div>
  );
}