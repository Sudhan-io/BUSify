import { useState } from 'react';
import { X, ShieldCheck } from 'lucide-react';
import { describeError } from '../services/auth';

/**
 * LoginModal — transport officer / admin sign-in.
 *
 * Rendered on demand rather than as a gate around the whole app: read-only
 * endpoints and the student commuter view are intentionally public, so an
 * unauthenticated visitor must still be able to use them.
 */
export default function LoginModal({ open, onClose, onAuthenticated }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  if (!open) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const session = await onAuthenticated(username.trim(), password);
      setUsername('');
      setPassword('');
      onClose();
      return session;
    } catch (err) {
      setError(describeError(err));
      return null;
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass =
    'w-full border border-[#dfe5df] rounded-lg px-3 py-2 text-sm text-[#18201d] ' +
    'focus:border-[#18201d] focus:outline-none focus-visible:outline-2 ' +
    'focus-visible:outline-offset-2 focus-visible:outline-[#ff6b00]';

  return (
    <div
      className="fixed inset-0 z-[1200] flex items-center justify-center bg-black/45 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="login-title"
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-sm rounded-2xl bg-white shadow-xl border border-[#e3e8e3] p-6"
        onKeyDown={(e) => {
          if (e.key === 'Escape') onClose();
        }}
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 id="login-title" className="text-lg font-bold text-[#18201d] flex items-center gap-2">
              <ShieldCheck size={18} aria-hidden="true" />
              Transport Officer Sign-in
            </h2>
            <p className="text-xs text-[#69716d] mt-1">
              Required for fleet, campus and simulation management.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close sign-in dialog"
            className="p-1 rounded hover:bg-[#f2f5f1] focus-visible:outline-2 focus-visible:outline-[#ff6b00]"
          >
            <X size={16} aria-hidden="true" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div>
            <label htmlFor="login-username" className="block text-[11px] font-semibold text-[#18201d] mb-1">
              Username *
            </label>
            <input
              id="login-username"
              name="username"
              type="text"
              autoComplete="username"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={inputClass}
            />
          </div>

          <div>
            <label htmlFor="login-password" className="block text-[11px] font-semibold text-[#18201d] mb-1">
              Password *
            </label>
            <input
              id="login-password"
              name="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
            />
          </div>

          {error && (
            <div role="alert" className="text-xs text-[#c0392b] bg-[#fdecea] border border-[#f5c6c2] rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="mt-1 bg-[#ff6b00] text-white rounded-lg px-4 py-2 text-sm font-semibold
                       disabled:opacity-60 disabled:cursor-not-allowed
                       focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#18201d]"
          >
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  );
}