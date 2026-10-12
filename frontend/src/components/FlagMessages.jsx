// The reasons the validators gave, in red for errors and amber for warnings
export default function FlagMessages({ flags }) {
  if (!flags || flags.length === 0) return null;
  return (
    <ul className="mt-1 space-y-0.5">
      {flags.map((flag, index) => (
        <li
          key={index}
          className={`text-sm ${flag.severity === "error" ? "text-red-700" : "text-amber-700"}`}
        >
          {flag.message}
        </li>
      ))}
    </ul>
  );
}
