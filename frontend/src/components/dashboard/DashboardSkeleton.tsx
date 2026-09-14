import React from 'react';

function Block({ className = '' }: { className?: string }) {
  return <div className={`bg-[#24313D]/40 rounded-xl animate-pulse ${className}`} />;
}

export function DashboardSkeleton() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
        <div className="space-y-2">
          <Block className="h-7 w-64" />
          <Block className="h-4 w-80" />
        </div>
        <Block className="h-10 w-72" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <Block className="h-[76px]" />
        <Block className="h-[76px]" />
        <Block className="h-[76px]" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Block className="lg:col-span-2 min-h-[400px]" />
        <div className="flex flex-col gap-6">
          <Block className="h-[248px]" />
          <Block className="h-[248px]" />
        </div>
      </div>
    </div>
  );
}