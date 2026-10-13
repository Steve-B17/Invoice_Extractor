import { useRef, useState } from "react";
import { toast } from "sonner";
import { exportCsv } from "../api/invoices";
import useOutsideClose from "../hooks/useOutsideClose";
import { secondaryButton } from "../ui";
import { saveBlob } from "../utils/download";
import { Download } from "./icons";

const OPTIONS = [
  { label: "Verified invoices", kind: "invoices", status: "VERIFIED" },
  { label: "Verified line items", kind: "items", status: "VERIFIED" },
  { label: "All invoices, any status", kind: "invoices", status: "ALL" },
];

export default function ExportMenu() {
  const menu = useRef(null);
  const [busy, setBusy] = useState(false);
  useOutsideClose(menu);

  async function download(option) {
    menu.current.open = false;
    setBusy(true);
    try {
      const { blob, filename } = await exportCsv(option);
      saveBlob(blob, filename);
      toast.success(`Downloaded ${filename}`);
    } catch {
      toast.error("The export failed. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <details ref={menu} className="relative">
      <summary
        className={`${secondaryButton} cursor-pointer list-none [&::-webkit-details-marker]:hidden`}
      >
        <Download className="h-4 w-4" />
        {busy ? "Exporting…" : "Export CSV"}
      </summary>
      <div className="absolute right-0 z-20 mt-2 w-60 rounded-2xl border border-slate-200 bg-white p-1.5 shadow-lg dark:border-slate-700/80 dark:bg-slate-800">
        {OPTIONS.map((option) => (
          <button
            key={option.label}
            type="button"
            disabled={busy}
            onClick={() => download(option)}
            className="block w-full rounded-xl px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            {option.label}
          </button>
        ))}
      </div>
    </details>
  );
}
