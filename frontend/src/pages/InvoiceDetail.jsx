import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { errorMessage } from "../api/client";
import { getInvoice } from "../api/invoices";
import StatusBadge from "../components/StatusBadge";
import { formatMoney } from "../utils/invoiceStats";

const FIELDS = [
  ["Vendor", "vendor_name"],
  ["GSTIN", "gstin"],
  ["Invoice number", "invoice_number"],
  ["Date", "invoice_date"],
  ["Subtotal", "subtotal", true],
  ["CGST", "cgst", true],
  ["SGST", "sgst", true],
  ["IGST", "igst", true],
  ["Round off", "round_off", true],
  ["Total", "total", true],
];

export default function InvoiceDetail() {
  const { id } = useParams();
  const { data, isLoading, error } = useQuery({
    queryKey: ["invoice", id],
    queryFn: () => getInvoice(id),
  });

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (error) {
    return (
      <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-red-700">
        {errorMessage(error, "Could not load this invoice")}
      </p>
    );
  }

  return (
    <div className="space-y-5">
      <Link
        to="/"
        className="text-sm font-medium text-indigo-600 hover:underline"
      >
        ← Back to invoices
      </Link>

      <div className="flex items-center justify-between gap-3">
        <h1 className="truncate text-xl font-semibold text-slate-900">
          {data.vendor_name ?? data.original_filename}
        </h1>
        <StatusBadge status={data.status} />
      </div>

      <dl className="grid gap-x-6 gap-y-3 rounded-xl bg-white p-4 shadow sm:grid-cols-2">
        {FIELDS.map(([label, key, isMoney]) => (
          <div key={key}>
            <dt className="text-sm text-slate-500">{label}</dt>
            <dd className="font-medium text-slate-900">
              {(isMoney ? formatMoney(data[key]) : data[key]) || "—"}
            </dd>
          </div>
        ))}
      </dl>

      {data.flags.length > 0 && (
        <ul className="space-y-2">
          {data.flags.map((flag, index) => (
            <li
              key={index}
              className={`rounded-lg px-3 py-2 text-sm ${
                flag.severity === "error"
                  ? "bg-red-50 text-red-800"
                  : "bg-amber-50 text-amber-800"
              }`}
            >
              <span className="font-medium">{flag.code}</span>: {flag.message}
            </li>
          ))}
        </ul>
      )}

      <p className="text-sm text-slate-500">
        The full review screen, with the bill image and editable fields, arrives
        in Part 3.
      </p>
    </div>
  );
}
