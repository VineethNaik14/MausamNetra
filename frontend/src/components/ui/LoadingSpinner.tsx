import React from 'react';
import { Loader2 } from 'lucide-react';

export function LoadingSpinner({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-8 min-h-[200px] w-full h-full text-[#34C759]/90">
      <Loader2 className="h-8 w-8 text-[#34C759]/90 animate-spin mb-4" />
      <p className="text-sm font-medium">{message}</p>
    </div>
  );
}
