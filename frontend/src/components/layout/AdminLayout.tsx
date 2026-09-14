import React from 'react';
import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { ShieldCheck, LogOut, LayoutDashboard, AlertCircle, CheckCircle, ChevronLeft } from 'lucide-react';
import { useAuth } from '../../services/AuthContext';
import { cn } from '../../lib/utils';

export function AdminLayout() {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navItems = [
    { name: 'Dashboard', path: '/admin', icon: LayoutDashboard },
    { name: 'Pending Review', path: '/admin/reports?status=Pending', icon: AlertCircle },
    { name: 'Verified', path: '/admin/reports?status=Verified', icon: CheckCircle },
  ];

  return (
    <div className="min-h-screen bg-[#24313D] bg-contour-lines flex flex-col md:flex-row-reverse text-[#F4F6F6]">
      {/* Sidebar */}
      <aside className="w-full md:w-64 bg-[#24313D] border-l border-[#34C759]/10 text-[#F4F6F6] flex flex-col shrink-0 relative z-20">
        <div className="h-16 flex items-center px-6 border-b border-[#34C759]/10">
          <Link to="/admin" className="flex items-center gap-3 text-[#F4F6F6] hover:text-[#34C759]/90 transition-colors">
            <ShieldCheck className="h-6 w-6 text-[#34C759]/90" />
            <span className="text-lg font-bold tracking-tight truncate">Admin Portal</span>
          </Link>
        </div>
        
        <div className="p-4 flex-1">
          <nav className="space-y-1.5 mt-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || location.search.includes(item.path.split('?')[1]);
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  className={cn(
                    "flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-all duration-200",
                    isActive 
                      ? "bg-[#34C759]/10 text-[#34C759] font-medium" 
                      : "text-[#34C759]/70 hover:bg-[#34C759] hover:text-[#1C2833]"
                  )}
                >
                  <Icon className={cn("h-4 w-4", isActive ? "text-[#34C759]/90" : "text-[#34C759]")} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="p-4 border-t border-[#34C759]/10">
          <div className="flex items-center gap-3 mb-4 px-2">
            <div className="h-9 w-9 rounded-full bg-[#24313D] border border-[#34C759]/40 flex items-center justify-center text-sm font-bold text-[#34C759]/90">
              {user?.name?.charAt(0) || 'A'}
            </div>
            <div className="overflow-hidden flex-1">
              <p className="text-sm font-medium text-[#F4F6F6] truncate">{user?.name}</p>
              <p className="text-xs text-[#34C759] truncate">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-[#34C759]/70 bg-transparent border border-[#34C759]/20 rounded-lg hover:bg-[#34C759] hover:text-[#1C2833] transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col w-full h-screen overflow-hidden">
        <header className="h-16 bg-[#24313D] border-b border-[#34C759]/20 flex items-center justify-between px-6 shadow-sm z-10 hidden md:flex">
          <Link 
            to="/" 
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium text-[#1C2833] bg-[#34C759] border border-[#34C759]/20 hover:bg-[#E8C15A] transition-all"
            title="Return to Public Site"
          >
            <ChevronLeft className="h-4 w-4" />
            <span>Back</span>
          </Link>
          <h1 className="text-xl font-semibold text-[#F4F6F6]">MausamNetra Command Center</h1>
        </header>
        <div className="flex-1 overflow-auto p-4 md:p-6 bg-[#24313D] bg-contour-lines">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
