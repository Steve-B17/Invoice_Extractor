import { MoonStar, SunMedium, Camera, FileText, ShieldCheck } from "./icons";
import Logo from "./Logo";
import { useTheme } from "../context/ThemeContext";

const POINTS = [
  { icon: Camera, text: "Snap a bill with your phone, or upload a PDF" },
  {
    icon: ShieldCheck,
    text: "Every number is double-checked by rules, not just AI",
  },
  { icon: FileText, text: "Review, fix, and export clean CSV for Excel" },
];

export default function AuthLayout({ title, subtitle, children, footer }) {
  const { theme, setTheme } = useTheme();

  return (
    <div className="grid min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-900 dark:text-slate-200 lg:grid-cols-2">
      <aside className="hidden flex-col justify-between bg-gradient-to-br from-indigo-700 via-indigo-600 to-violet-600 p-12 text-white lg:flex">
        <Logo light />
        <div className="space-y-8">
          <h2 className="text-4xl font-bold leading-tight tracking-tight text-white">
            Turn paper bills into clean, checked data.
          </h2>
          <ul className="space-y-4 text-indigo-50">
            {POINTS.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-indigo-50">
                <span className="rounded-xl bg-white/15 p-2">
                  <Icon className="h-5 w-5" />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </div>
        <p className="text-sm text-indigo-200">GST invoices in English and Tamil.</p>
      </aside>

      <main className="flex items-center justify-center bg-slate-50 px-4 py-10 dark:bg-slate-900">
        <div className="fade-in-up w-full max-w-sm space-y-6">
          <div className="flex items-center justify-between gap-3">
            <div className="lg:hidden">
              <Logo />
            </div>
            <div className="ml-auto">
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
            </div>
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-200">
              {title}
            </h1>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{subtitle}</p>
          </div>
          {children}
          <p className="text-center text-sm text-slate-600 dark:text-slate-400">{footer}</p>
        </div>
      </main>
    </div>
  );
}
