import { useRef } from "react";
import { useAuth } from "../context/AuthContext";
import useOutsideClose from "../hooks/useOutsideClose";
import { initialsFor } from "../utils/invoiceStats";
import { LogOut } from "./icons";

export default function UserMenu() {
  const { user, logout } = useAuth();
  const menu = useRef(null);
  useOutsideClose(menu);

  return (
    <details ref={menu} className="relative">
      <summary
        aria-label="Account menu"
        className="flex h-9 w-9 cursor-pointer list-none items-center justify-center rounded-full bg-indigo-100 text-sm font-semibold text-indigo-700 hover:bg-indigo-200 dark:bg-indigo-500/15 dark:text-indigo-200 dark:hover:bg-indigo-500/25 [&::-webkit-details-marker]:hidden"
      >
        {initialsFor(user?.email)}
      </summary>
      <div className="absolute right-0 z-40 mt-2 w-64 rounded-2xl border border-slate-200 bg-white p-2 shadow-lg dark:border-slate-700/80 dark:bg-slate-800">
        <p className="truncate px-3 py-2 text-sm text-slate-500 dark:text-slate-300">
          {user?.email}
        </p>
        <button
          type="button"
          onClick={logout}
          className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          <LogOut className="h-4 w-4" />
          Log out
        </button>
      </div>
    </details>
  );
}
