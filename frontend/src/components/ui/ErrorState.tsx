import React from 'react';
import { AlertCircle } from 'lucide-react';

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({ message = 'Something went wrong while loading data.', onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 bg-[#1C2833]/60 rounded-xl border border-red-400/20 min-h-[200px] w-full">
      <AlertCircle className="h-10 w-10 text-red-400 mb-4" />
      <p className="text-sm text-[#F4F6F6]/90 font-medium text-center mb-1">{message}</p>
      <p className="text-xs text-[#34C759]/60 text-center mb-5">Check your connection and try again.</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-[#34C759] hover:bg-[#E8C15A] text-[#24313D] rounded-lg text-sm font-medium transition-colors shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#34C759] focus-visible:ring-offset-2 focus-visible:ring-offset-[#1C2833]"
        >
          Try again
        </button>
      )}
    </div>
  );
}
