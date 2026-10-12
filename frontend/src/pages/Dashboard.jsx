import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import { errorMessage } from "../api/client";
import { listInvoices, reprocessInvoice } from "../api/invoices";
import Spinner from "../components/Spinner";
import StatusBadge from "../components/StatusBadge";
import { primaryButton, secondaryButton } from "../ui";
import {
  STATUS_FILTERS,
  countByStatus,
  filterByStatus,
  flagCounts,
  formatMoney,
  hasProcessing,
} from "../utils/invoiceStats";

function Stat({ label, value }) {
  return (
    <div className="rounded-xl bg-white px-4 py-3 shadow-sm">
      <p className="text-2xl font-semibold text-slate-900">{value}</p>
      <p className="text-sm text-slate-500">{label}</p>
    </div>
  );
}

function FlagChips({ invoice }) {
  const { errors, warnings } = flagCounts(invoice);
  if (invoice.status === "NEEDS_REVIEW" && errors === 0 && warnings === 0) {
    return (
      <span className="rounded-full bg-green-50 px-2 py-0.5 text-xs text-green-700">
        No issues found
      </span>
    );
  }
  return (
    <>
      {errors > 0 && (
        <span className="rounded-full bg-red-50 px-2 py-0.5 text-xs text-red-700">
          {errors} {errors === 1 ? "error" : "errors"}
        </span>
      )}
      {warnings > 0 && (
        <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-700">
          {warnings} {warnings === 1 ? "warning" : "warnings"}
        </span>
      )}
    </>
  );
}

export default function Dashboard() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState("ALL");

  const { data, isLoading, error } = useQuery({
    queryKey: ["invoices"],
    queryFn: listInvoices,
    // TanStack Query v5: refetch every 3 seconds while any bill is still being processed
    refetchInterval: (query) =>
      hasProcessing(query.state.data) ? 3000 : false,
  });

  const retry = useMutation({
    mutationFn: reprocessInvoice,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["invoices"] }),
  });

  if (isLoading) return <p className="text-slate-500">Loading invoices…</p>;
  if (error) {
    return (
      <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-red-700">
        {errorMessage(error, "Could not load invoices")}
      </p>
    );
  }

  const counts = countByStatus(data);
  const visible = filterByStatus(data, filter);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold text-slate-900">Invoices</h1>
        <Link to="/upload" className={primaryButton}>
          Upload bill
        </Link>
      </div>

      {data.length === 0 ? (
        <div className="rounded-2xl bg-white p-8 text-center shadow-sm">
          <p className="mb-4 text-slate-700">
            No invoices yet. Upload your first bill to get started.
          </p>
          <Link to="/upload" className={primaryButton}>
            Upload bill
          </Link>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-3">
            <Stat label="Total" value={counts.ALL} />
            <Stat label="Needs review" value={counts.NEEDS_REVIEW} />
            <Stat label="Verified" value={counts.VERIFIED} />
          </div>

          <div className="flex flex-wrap gap-2">
            {STATUS_FILTERS.map(({ key, label }) => (
              <button
                key={key}
                type="button"
                onClick={() => setFilter(key)}
                className={`rounded-full px-3 py-1 text-sm font-medium ${
                  filter === key
                    ? "bg-indigo-600 text-white"
                    : "bg-white text-slate-700 shadow-sm hover:bg-slate-100"
                }`}
              >
                {label} ({counts[key]})
              </button>
            ))}
          </div>

          {retry.error && (
            <p
              role="alert"
              className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700"
            >
              {errorMessage(retry.error, "Could not restart processing")}
            </p>
          )}

          {visible.length === 0 ? (
            <p className="text-slate-500">Nothing in this group.</p>
          ) : (
            <ul className="divide-y rounded-xl bg-white shadow">
              {visible.map((invoice) => (
                <li key={invoice.id}>
                  <Link
                    to={`/invoices/${invoice.id}`}
                    className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-slate-50"
                  >
                    <div className="min-w-0 space-y-1">
                      <p className="truncate font-medium text-slate-900">
                        {invoice.vendor_name ?? invoice.original_filename}
                      </p>
                      <p className="text-sm text-slate-500">
                        {new Date(invoice.created_at).toLocaleString("en-IN", {
                          dateStyle: "medium",
                          timeStyle: "short",
                        })}
                        {invoice.total
                          ? ` · ${formatMoney(invoice.total)}`
                          : ""}
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        <FlagChips invoice={invoice} />
                      </div>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      {invoice.status === "PROCESSING" && (
                        <Spinner label="Reading the bill" />
                      )}
                      <StatusBadge status={invoice.status} />
                    </div>
                  </Link>

                  {invoice.status === "FAILED" && (
                    <div className="flex flex-wrap items-center gap-3 px-4 pb-3">
                      <p className="text-sm text-red-600">
                        {invoice.error_message}
                      </p>
                      <button
                        type="button"
                        className={secondaryButton}
                        disabled={
                          retry.isPending && retry.variables === invoice.id
                        }
                        onClick={() => retry.mutate(invoice.id)}
                      >
                        Try again
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}
