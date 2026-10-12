import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { secondaryButton } from "../ui";

const linkClass = ({ isActive }) =>
  `rounded-md px-3 py-1.5 text-sm font-medium ${
    isActive
      ? "bg-indigo-50 text-indigo-700"
      : "text-slate-600 hover:bg-slate-100"
  }`;

export default function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-2 px-4 py-3">
          <div className="flex items-center gap-4">
            <span className="text-lg font-semibold text-slate-900">
              Invoice Extractor
            </span>
            <nav className="flex gap-1">
              <NavLink to="/" end className={linkClass}>
                Invoices
              </NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-slate-500 sm:inline">
              {user?.email}
            </span>
            <button type="button" className={secondaryButton} onClick={logout}>
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
