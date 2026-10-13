export default function FormField({ label, error, children }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-slate-700 dark:text-slate-200">
        {label}
      </span>
      {children}
      {error && (
        <span className="mt-1 block text-sm text-rose-600 dark:text-rose-400">
          {error}
        </span>
      )}
    </label>
  );
}
