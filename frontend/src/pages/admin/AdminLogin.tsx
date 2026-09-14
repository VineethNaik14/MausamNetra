import React, { useState } from 'react';
import { useNavigate, Navigate, Link } from 'react-router-dom';
import { useAuth } from '../../services/AuthContext';
import { authApi } from '../../services/api';
import { ShieldCheck, Lock, Mail, AlertCircle, ArrowLeft, Eye, EyeOff } from 'lucide-react';
export default function AdminLogin() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  if (user && user.role === 'ADMIN') {
    return <Navigate to="/admin" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await authApi.login({ email, password });
      if (res.data.user.role !== 'ADMIN') {
        setError('This account does not have admin privileges');
        setLoading(false);
        return;
      }
      login(res.data.token, res.data.user);
      navigate('/admin', { replace: true });
    } catch (err) {
      setError('Invalid credentials');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#24313D] bg-contour-lines flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center mb-6">
          <Link
            to="/"
            className="absolute top-6 left-6 inline-flex items-center gap-2 px-4 py-2 bg-[#24313D] border border-[#34C759]/30 rounded-md text-[#34C759] text-sm font-medium hover:bg-[#34C759] hover:text-[#1C2833] hover:border-[#34C759] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#34C759] focus-visible:ring-offset-2 focus-visible:ring-offset-[#1C2833]"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </Link>
        </div>
        <div className="flex justify-center">
          <div className="bg-[#24313D] p-3 rounded-xl">
            <ShieldCheck className="h-8 w-8 text-[#F4F6F6]" />
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-extrabold text-[#F4F6F6]">
          Admin Portal
        </h2>
        <p className="mt-2 text-center text-sm text-[#34C759]/70">
          Sign in to access MausamNetra command center
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-[#24313D] py-8 px-4 shadow sm:rounded-lg sm:px-10 border border-[#34C759]/20">
          {error && (
            <div className="mb-4 p-3 bg-red-900/30 text-red-400 rounded-md flex items-center gap-2 text-sm border border-red-900/50">
              <AlertCircle className="h-4 w-4" />
              {error}
            </div>
          )}

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label className="block text-sm font-medium text-[#34C759]/90">
                Email address
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-[#34C759]" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="focus:ring-[#34C759] focus:border-[#34C759]/40 block w-full pl-10 sm:text-sm bg-[#24313D] border-[#34C759]/40 text-[#F4F6F6] rounded-md py-2 border"
                  placeholder="Mail ID"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-[#34C759]/90">
                Password
              </label>
              <div className="mt-1 relative rounded-md shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-[#34C759]" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="focus:ring-[#34C759] focus:border-[#34C759]/40 block w-full pl-10 pr-10 sm:text-sm bg-[#24313D] border-[#34C759]/40 text-[#F4F6F6] rounded-md py-2 border"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-[#34C759] hover:text-[#F4F6F6] transition-colors focus:outline-none"
                  tabIndex={-1}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-[#1C2833] bg-[#34C759] hover:bg-[#E8C15A] hover:text-[#1C2833]/80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#34C759] disabled:bg-[#1C2833]/80 transition-colors"
              >
                {loading ? 'Signing in...' : 'Sign in'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
