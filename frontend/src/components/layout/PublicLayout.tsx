import React, { useState } from 'react';
import { Link, Outlet, useNavigate } from 'react-router-dom';
import {
  CloudRain,
  AlertTriangle,
  ShieldCheck,
  Menu,
  LogOut,
} from 'lucide-react';
import { useAuth } from '../../services/AuthContext';
import { useEffect, useRef} from 'react';

export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  function handleClickOutside(event: MouseEvent) {
    if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
      setMenuOpen(false);
    }
  }
  function handleEscape(event: KeyboardEvent) {
    if (event.key === 'Escape') setMenuOpen(false);
  }
  if (menuOpen) {
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
  }
  return () => {
    document.removeEventListener('mousedown', handleClickOutside);
    document.removeEventListener('keydown', handleEscape);
  };
}, [menuOpen]);

  const handleLogout = () => {
    logout();
    setMenuOpen(false);
    navigate('/');
  };

  return (
    <nav className="bg-[#24313D] border-b border-[#34C759]/20 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">

          {/* Logo */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-2">
              <div className="bg-[#34C759] p-2 rounded-lg">
                <CloudRain className="h-6 w-6 text-[#1C2833]" />
              </div>

              <span className="text-xl font-bold text-[#F4F6F6] tracking-tight">
                MausamNetra
              </span>
            </Link>
          </div>

          {/* Right Side */}
          <div ref={menuRef} className="flex items-center gap-4 relative">

            {/* Report Incident */}
            <Link
              to="/report"
              className="hidden sm:inline-flex items-center gap-2 px-4 py-2 bg-[#34C759] text-[#1C2833] text-sm font-medium rounded-md hover:bg-[#E8C15A] hover:text-[#1C2833]/80 transition-colors shadow-sm"
            >
              <AlertTriangle className="h-4 w-4" />
              Report Incident
            </Link>

            {/* Menu Button */}
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="p-2 text-[#34C759] hover:text-[#1C2833] hover:bg-[#34C759] rounded-md transition-colors flex items-center gap-2"
              aria-label="Open menu"
              aria-expanded={menuOpen}
            >
              <Menu className="h-6 w-6" />
            </button>

            {/* Dropdown Menu */}
            {menuOpen && (
              <div className="absolute right-0 top-14 mt-1 w-56 bg-[#24313D] border border-[#34C759]/40 rounded-md shadow-xl overflow-hidden flex flex-col z-50">

                {user ? (
                  <>
                    {/* User Information */}
                    <div className="px-4 py-3 border-b border-[#34C759]/20 text-sm">
                      <p className="text-[#34C759]/70">
                        Signed in as
                      </p>

                      <p className="font-medium text-[#F4F6F6] truncate">
                        {user.name}
                      </p>
                    </div>

                    {/* Admin Dashboard */}
                    {user.role === 'ADMIN' && (
                      <Link
                        to="/admin"
                        onClick={() => setMenuOpen(false)}
                        className="flex items-center gap-3 px-4 py-3 text-sm text-[#34C759]/90 hover:bg-[#34C759] hover:text-[#1C2833] transition-colors"
                      >
                        <ShieldCheck className="h-4 w-4" />
                        Admin Dashboard
                      </Link>
                    )}

                    {/* Sign Out */}
                    <button
                      onClick={handleLogout}
                      className="flex items-center gap-3 px-4 py-3 text-sm text-red-400 hover:bg-[#34C759] hover:text-red-900 transition-colors text-left w-full"
                    >
                      <LogOut className="h-4 w-4" />
                      Sign Out
                    </button>
                  </>
                ) : (
                  <>
                    {/* Admin Login */}
                    <Link
                      to="/admin/login"
                      onClick={() => setMenuOpen(false)}
                      className="flex items-center gap-3 px-4 py-3 text-sm text-[#34C759]/90 hover:bg-[#34C759] hover:text-[#1C2833] transition-colors"
                    >
                      <ShieldCheck className="h-4 w-4" />
                      Admin Login
                    </Link>
                  </>
                )}

              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

export function PublicLayout() {
  return (
    <div className="min-h-screen bg-[#24313D] bg-contour-lines text-[#F4F6F6] flex flex-col">
      <Navbar />

      <main className="flex-1 w-full">
        <Outlet />
      </main>
    </div>
  );
}