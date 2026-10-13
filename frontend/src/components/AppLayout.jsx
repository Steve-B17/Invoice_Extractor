import { Link, Outlet } from "react-router-dom";
import { useTheme } from "../context/ThemeContext";
import { MoonStar, SunMedium } from "./icons";
import Logo from "./Logo";
import UserMenu from "./UserMenu";

export default function AppLayout() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-white/80 backdrop-blur dark:border-slate-700/80 dark:bg-slate-800/90">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4">
          <Link to="/" aria-label="Invoice Extractor home">
            <Logo />
          </Link>
          <div className="flex items-center gap-2">
            <button
              type="button"
              aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-700 dark:text-slate-200 dark:hover:bg-slate-600"
            >
              {theme === "dark" ? (
                <SunMedium className="h-4 w-4" />
              ) : (
                <MoonStar className="h-4 w-4" />
              )}
            </button>
            <UserMenu />
          </div>
        </div>
      </header>

      <main className="fade-in-up mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
