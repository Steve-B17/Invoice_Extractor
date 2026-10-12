import { useQuery } from "@tanstack/react-query";
import { errorMessage } from "../api/client";
import { listInvoices } from "../api/invoices";
import StatusBadge from "../components/StatusBadge";

export default function Dashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["invoices"],
    queryFn: listInvoices,
  });

  if (isLoading) return <p className="text-slate-500">Loading invoices…</p>;
  if (error) {
    return (
      <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-red-700">
        {errorMessage(error, "Could not load invoices")}
      </p>
    );
  }
  if (data.length === 0) {
    return (
      <p className="text-slate-600">
        No invoices yet. Uploading arrives in the next part.
      </p>
    );
  }

  return (
    <div>
      <h1 className="mb-4 text-xl font-semibold text-slate-900">
        Your invoices ({data.length})
      </h1>
      <ul className="divide-y rounded-xl bg-white shadow">
        {data.map((invoice) => (
          <li
            key={invoice.id}
            className="flex items-center justify-between gap-3 px-4 py-3"
          >
            <div className="min-w-0">
              <p className="truncate font-medium text-slate-900">
                {invoice.vendor_name ?? invoice.original_filename}
              </p>
              <p className="text-sm text-slate-500">
                {new Date(invoice.created_at).toLocaleString()}
                {invoice.total ? ` · Rs ${invoice.total}` : ""}
              </p>
            </div>
            <StatusBadge status={invoice.status} />
          </li>
        ))}
      </ul>
    </div>
  );
}
