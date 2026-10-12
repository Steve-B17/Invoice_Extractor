const STYLES = {
  PROCESSING: "bg-amber-100 text-amber-800",
  NEEDS_REVIEW: "bg-blue-100 text-blue-800",
  VERIFIED: "bg-green-100 text-green-800",
  FAILED: "bg-red-100 text-red-800",
};

const LABELS = {
  PROCESSING: "Processing",
  NEEDS_REVIEW: "Needs review",
  VERIFIED: "Verified",
  FAILED: "Failed",
};

export default function StatusBadge({ status }) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${
        STYLES[status] ?? "bg-slate-100 text-slate-700"
      }`}
    >
      {LABELS[status] ?? status}
    </span>
  );
}
