const focusRing =
  "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600";

const buttonBase =
  "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold " +
  "transition active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60 " +
  `disabled:active:scale-100 ${focusRing}`;

export const primaryButton = `${buttonBase} bg-indigo-600 text-white shadow-sm hover:bg-indigo-700`;
export const secondaryButton = `${buttonBase} border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700`;
export const successButton = `${buttonBase} bg-emerald-600 text-white shadow-sm hover:bg-emerald-700`;
export const dangerButton = `${buttonBase} bg-rose-600 text-white shadow-sm hover:bg-rose-700`;
export const ghostButton = `${buttonBase} text-slate-600 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800`;

export const cardClass =
  "rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-700/80 dark:bg-slate-800";

const inputBase =
  "w-full rounded-xl border px-3 py-2 text-base outline-none transition focus:ring-2 dark:text-slate-200";

export const inputClass = `${inputBase} border-slate-300 bg-white focus:border-indigo-500 focus:ring-indigo-200 dark:border-slate-700 dark:bg-slate-800 dark:focus:border-indigo-400 dark:focus:ring-indigo-900/80`;

// Input style for a field that has validation flags
export function fieldClass(severity) {
  if (severity === "error") {
    return `${inputBase} border-rose-400 bg-rose-50 focus:border-rose-500 focus:ring-rose-200 dark:border-rose-500 dark:bg-rose-950/40 dark:focus:border-rose-400 dark:focus:ring-rose-900/80`;
  }
  if (severity === "warning") {
    return `${inputBase} border-amber-400 bg-amber-50 focus:border-amber-500 focus:ring-amber-200 dark:border-amber-500 dark:bg-amber-950/40 dark:focus:border-amber-400 dark:focus:ring-amber-900/80`;
  }
  return inputClass;
}
