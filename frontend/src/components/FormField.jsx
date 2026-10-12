export default function FormField({ label, error, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </span>
      {children}
      {error && (
        <span className="mt-1 block text-sm text-red-600">{error}</span>
      )}
    </label>
  );
}
