'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { ShieldCheck, AlertTriangle, Loader2 } from 'lucide-react';

function CallbackHandler() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = searchParams.get('token');
    const refreshToken = searchParams.get('refresh_token');
    const err = searchParams.get('error');

    if (err) {
      const errorMessages: Record<string, string> = {
        access_denied: 'Google sign-in was cancelled.',
        invalid_state: 'Security validation failed (invalid state token). Please try again.',
        token_exchange_failed: 'Failed to exchange authorization code with Google.',
        userinfo_failed: 'Could not retrieve verified profile from Google.',
        unverified_email: 'Your Google email address is not verified.',
        server_error: 'A server error occurred during authentication.',
      };
      setError(errorMessages[err] || `Authentication failed: ${err}`);
      return;
    }

    if (token) {
      try {
        api.setToken(token);
        if (refreshToken) {
          localStorage.setItem('ccs_refresh_token', refreshToken);
        }
        // Redirect to main command center
        router.replace('/');
      } catch (e: any) {
        setError('Failed to store authentication token locally.');
      }
    } else {
      setError('No authentication token received from identity provider.');
    }
  }, [searchParams, router]);

  if (error) {
    return (
      <div className="min-h-screen bg-canvas-950 flex items-center justify-center p-4">
        <div className="bg-canvas-900 border border-crimson-500/30 rounded-2xl p-8 max-w-md w-full text-center shadow-2xl">
          <div className="w-14 h-14 bg-crimson-500/10 border border-crimson-500/20 text-crimson-400 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <AlertTriangle className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold text-slate-100 mb-2">Authentication Failed</h2>
          <p className="text-sm text-slate-400 mb-6">{error}</p>
          <button
            onClick={() => router.push('/')}
            className="w-full py-2.5 px-4 bg-navy-700 hover:bg-navy-600 border border-navy-500 text-slate-200 rounded-xl text-sm font-semibold transition-colors"
          >
            Return to Command Center
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-canvas-950 flex items-center justify-center p-4">
      <div className="bg-canvas-900 border border-navy-800 rounded-2xl p-8 max-w-md w-full text-center shadow-2xl">
        <div className="w-14 h-14 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded-2xl flex items-center justify-center mx-auto mb-4 animate-pulse">
          <ShieldCheck className="w-7 h-7" />
        </div>
        <h2 className="text-xl font-bold text-slate-100 mb-1">ColdChain Sentinel</h2>
        <p className="text-sm text-slate-400 mb-4">Authenticating identity with Google...</p>
        <div className="flex items-center justify-center gap-2 text-xs text-cyan-400">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Verifying cryptographic tokens...</span>
        </div>
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-canvas-950 flex items-center justify-center p-4">
          <div className="text-slate-400 text-sm">Loading security context...</div>
        </div>
      }
    >
      <CallbackHandler />
    </Suspense>
  );
}
