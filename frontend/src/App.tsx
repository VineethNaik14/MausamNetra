/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './services/AuthContext';
import { PublicLayout } from './components/layout/PublicLayout';
import { AdminLayout } from './components/layout/AdminLayout';
import { LoadingSpinner } from './components/ui/LoadingSpinner';

import PublicDashboard from './pages/PublicDashboard';
import IncidentDetail from './pages/IncidentDetail';
import ReportSubmission from './pages/ReportSubmission';
import AdminLogin from './pages/admin/AdminLogin';
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminReportReview from './pages/admin/AdminReportReview';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  
  if (loading) return <div className="h-screen w-screen bg-[#24313D] bg-contour-lines flex items-center justify-center"><LoadingSpinner /></div>;
  
  if (!user || user.role !== 'ADMIN') {
    return <Navigate to="/admin/login" replace />;
  }
  
  return <>{children}</>;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route element={<PublicLayout />}>
            <Route path="/" element={<PublicDashboard />} />
            <Route path="/events/:id" element={<IncidentDetail />} />
            <Route path="/report" element={<ReportSubmission />} />
          </Route>

          {/* Login Routes (no layout) */}
          <Route path="/admin/login" element={<AdminLogin />} />

          {/* Protected Admin Routes */}
          <Route path="/admin" element={
            <ProtectedRoute>
              <AdminLayout />
            </ProtectedRoute>
          }>
            <Route index element={<AdminDashboard />} />
            <Route path="reports/:id" element={<AdminReportReview />} />
            <Route path="reports" element={<AdminDashboard />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
