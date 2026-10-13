import { TriangleAlert } from "./icons";

// The reasons the validators gave, in rose for errors and amber for warnings
export default function FlagMessages({ flags }) {
  if (!flags || flags.length === 0) return null;
  return (
    <ul className="mt-1.5 space-y-1">
      {flags.map((flag, index) => (
        <li
          key={index}
          className={`flex items-start gap-1.5 text-sm ${
            flag.severity === "error" ? "text-rose-700" : "text-amber-700"
          }`}
        >
          <TriangleAlert
            className="mt-0.5 h-4 w-4 shrink-0"
            aria-hidden="true"
          />
          <span>{flag.message}</span>
        </li>
      ))}
    </ul>
  );
}
