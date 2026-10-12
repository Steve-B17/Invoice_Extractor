const inputBase =
  "w-full rounded-lg border px-3 py-2 text-base outline-none focus:ring-2";

export const inputClass = `${inputBase} border-slate-300 focus:border-indigo-500 focus:ring-indigo-200`;

// Input style for a field that has validation flags
export function fieldClass(severity) {
  if (severity === "error") {
    return `${inputBase} border-red-400 bg-red-50 focus:border-red-500 focus:ring-red-200`;
  }
  if (severity === "warning") {
    return `${inputBase} border-amber-400 bg-amber-50 focus:border-amber-500 focus:ring-amber-200`;
  }
  return inputClass;
}

export const primaryButton =
  "inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 " +
  "font-medium text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60";

export const secondaryButton =
  "inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-4 py-2 " +
  "font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60";

export const successButton =
  "inline-flex items-center justify-center rounded-lg bg-green-600 px-4 py-2 " +
  "font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60";
