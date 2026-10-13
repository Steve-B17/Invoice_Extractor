export default function Logo({ light = false, className = "" }) {
  return (
    <span className={`inline-flex items-center gap-2 ${className}`}>
      <svg viewBox="0 0 32 32" className="h-8 w-8" aria-hidden="true">
        <rect
          width="32"
          height="32"
          rx="9"
          fill={light ? "#ffffff" : "#4f46e5"}
        />
        <path
          d="M10 8h8l4 4v12a1 1 0 0 1-1 1H10a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z"
          fill={light ? "#4f46e5" : "#ffffff"}
          opacity="0.95"
        />
        <path
          d="M12.5 17.5l2.2 2.2 4.3-4.6"
          fill="none"
          stroke={light ? "#ffffff" : "#4f46e5"}
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span
        className={`text-lg font-bold tracking-tight ${light ? "text-white" : "text-slate-900 dark:text-slate-200"}`}
      >
        Invoice
        <span className={light ? "text-indigo-200" : "text-indigo-600 dark:text-indigo-400"}>
          Extractor
        </span>
      </span>
    </span>
  );
}
