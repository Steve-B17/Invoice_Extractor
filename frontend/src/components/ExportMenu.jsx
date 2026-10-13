import { useRef, useState } from "react";
import { exportCsv } from "../api/invoices";
import { secondaryButton } from "../ui";
import { saveBlob } from "../utils/download";

const OPTIONS = [
  { label: "Verified invoices", kind: "invoices", status: "VERIFIED" },
  { label: "Verified line items", kind: "items", status: "VERIFIED" },
  { label: "All invoices, any status", kind: "invoices", status: "ALL" },
];

export default function ExportMenu() {
  const menu = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function download(option) {
    menu.current.open = false;
    setBusy(true);
    setError("");
    try {
      const { blob, filename } = await exportCsv(option);
      saveBlob(blob, filename);
    } catch {
      setError("The export failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="relative">
      <details ref={menu}>
        <summary className={`${secondaryButton} cursor-pointer list-none`}>
          {busy ? "Exporting…" : "Export CSV"}
        </summary>
        <div className="absolute right-0 z-10 mt-2 w-60 rounded-xl border bg-white p-1 shadow-lg">
          {OPTIONS.map((option) => (
            <button
              key={option.label}
              type="button"
              disabled={busy}
              onClick={() => download(option)}
              className="block w-full rounded-lg px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
            >
              {option.label}
            </button>
          ))}
        </div>
      </details>
      {error && (
        <p
          role="alert"
          className="absolute right-0 mt-2 w-60 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700"
        >
          {error}
        </p>
      )}
    </div>
  );
}
