import { Clock, Eye, ShieldCheck, X } from "./icons";

const STYLES = {
  PROCESSING:
    "bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-500/10 dark:text-amber-300 dark:ring-amber-500/30",
  NEEDS_REVIEW:
    "bg-sky-50 text-sky-700 ring-sky-200 dark:bg-sky-500/10 dark:text-sky-300 dark:ring-sky-500/30",
  VERIFIED:
    "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-300 dark:ring-emerald-500/30",
  FAILED:
    "bg-rose-50 text-rose-700 ring-rose-200 dark:bg-rose-500/10 dark:text-rose-300 dark:ring-rose-500/30",
  default:
    "bg-slate-100 text-slate-700 ring-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:ring-slate-700",
};

const LABELS = {
  PROCESSING: "Processing",
  NEEDS_REVIEW: "Needs review",
  VERIFIED: "Verified",
  FAILED: "Failed",
};

const ICONS = {
  PROCESSING: Clock,
  NEEDS_REVIEW: Eye,
  VERIFIED: ShieldCheck,
  FAILED: X,
};

export default function StatusBadge({ status }) {
  const Icon = ICONS[status];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${
        STYLES[status] ?? STYLES.default
      }`}
    >
      {Icon && <Icon className="h-3.5 w-3.5" aria-hidden="true" />}
      {LABELS[status] ?? status}
    </span>
  );
}
