import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { errorMessage } from "../api/client";
import { listInvoices, reprocessInvoice } from "../api/invoices";
import ExportMenu from "../components/ExportMenu";
import {
  ChevronRight,
  Clock,
  Eye,
  FileText,
  Inbox,
  RefreshCw,
  Search,
  ShieldCheck,
  TriangleAlert,
  UploadIcon,
  X,
} from "../components/icons";
import Skeleton from "../components/Skeleton";
import Spinner from "../components/Spinner";
import StatusBadge from "../components/StatusBadge";
import useDocumentTitle from "../hooks/useDocumentTitle";
import { cardClass, inputClass, primaryButton, secondaryButton } from "../ui";
import {
  SORT_OPTIONS,
  countByStatus,
  filterByStatus,
  flagCounts,
  formatMoney,
  hasProcessing,
  searchInvoices,
  sortInvoices,
  timeAgo,
} from "../utils/invoiceStats";

const STATS = [
  {
    key: "ALL",
    label: "Total invoices",
    icon: FileText,
    tone: "bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-300",
  },
  {
    key: "NEEDS_REVIEW",
    label: "Need review",
    icon: Eye,
    tone: "bg-sky-50 text-sky-600 dark:bg-sky-500/10 dark:text-sky-300",
  },
  {
    key: "VERIFIED",
    label: "Verified",
    icon: ShieldCheck,
    tone: "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-300",
  },
  {
    key: "FAILED",
    label: "Failed",
    icon: TriangleAlert,
    tone: "bg-rose-50 text-rose-600 dark:bg-rose-500/10 dark:text-rose-300",
  },
];

const ROW_ICON = {
  PROCESSING: { icon: Clock, tone: "bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-300" },
  NEEDS_REVIEW: { icon: Eye, tone: "bg-sky-50 text-sky-600 dark:bg-sky-500/10 dark:text-sky-300" },
  VERIFIED: { icon: ShieldCheck, tone: "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-300" },
  FAILED: { icon: TriangleAlert, tone: "bg-rose-50 text-rose-600 dark:bg-rose-500/10 dark:text-rose-300" },
};

function StatCard({ stat, value, active, onClick }) {
  const Icon = stat.icon;
  return (
    <button
      type="button"
      onClick={onClick}
      className={`${cardClass} flex items-center gap-3 p-4 text-left transition hover:shadow-md ${
        active ? "ring-2 ring-indigo-500" : ""
      }`}
    >
      <span className={`rounded-xl p-2.5 ${stat.tone}`}>
        <Icon className="h-5 w-5" />
      </span>
      <span>
        <span className="block text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-200">
          {value}
        </span>
        <span className="text-sm text-slate-500 dark:text-slate-400">{stat.label}</span>
      </span>
    </button>
  );
}

function FlagChips({ invoice }) {
  const { errors, warnings } = flagCounts(invoice);
  if (invoice.status === "NEEDS_REVIEW" && errors === 0 && warnings === 0) {
    return (
      <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">
        No issues found
      </span>
    );
  }
  return (
    <>
      {errors > 0 && (
        <span className="rounded-full bg-rose-50 px-2 py-0.5 text-xs text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
          {errors} {errors === 1 ? "error" : "errors"}
        </span>
      )}
      {warnings > 0 && (
        <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-700 dark:bg-amber-500/10 dark:text-amber-300">
          {warnings} {warnings === 1 ? "warning" : "warnings"}
        </span>
      )}
    </>
  );
}

function SkeletonList() {
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {[0, 1, 2, 3].map((index) => (
          <Skeleton key={index} className="h-20 rounded-2xl" />
        ))}
      </div>
      <div className={`${cardClass} divide-y divide-slate-100 dark:divide-slate-700/70`}>
        {[0, 1, 2, 3].map((index) => (
          <div key={index} className="flex items-center gap-3 p-4">
            <Skeleton className="h-10 w-10 rounded-xl" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="h-3 w-1/4" />
            </div>
            <Skeleton className="h-6 w-24 rounded-full" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Dashboard() {
  useDocumentTitle("Invoices");
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("newest");

  const { data, isLoading, error } = useQuery({
    queryKey: ["invoices"],
    queryFn: listInvoices,
    // TanStack Query v5: refetch every 3 seconds while any bill is still being processed
    refetchInterval: (query) =>
      hasProcessing(query.state.data) ? 3000 : false,
  });

  const retry = useMutation({
    mutationFn: reprocessInvoice,
    onSuccess: () => {
      toast.success("Reading the bill again");
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
    },
    onError: (failure) =>
      toast.error(errorMessage(failure, "Could not restart processing")),
  });

  const counts = useMemo(() => countByStatus(data ?? []), [data]);
  const visible = useMemo(
    () =>
      sortInvoices(
        searchInvoices(filterByStatus(data ?? [], filter), search),
        sort,
      ),
    [data, filter, search, sort],
  );

  if (isLoading) return <SkeletonList />;
  if (error) {
    return (
      <p
        role="alert"
        className="rounded-xl bg-rose-50 px-4 py-3 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300"
      >
        {errorMessage(error, "Could not load invoices")}
      </p>
    );
  }

  const filtering = filter !== "ALL" || search.trim() !== "";

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
      <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-200">
          Invoices
        </h1>
        <div className="flex items-center gap-2">
          <ExportMenu />
          <Link to="/upload" className={primaryButton}>
            <UploadIcon className="h-4 w-4" />
            Upload bill
          </Link>
        </div>
      </div>

      {data.length === 0 ? (
        <div
          className={`${cardClass} flex flex-col items-center gap-3 p-10 text-center`}
        >
          <span className="rounded-2xl bg-indigo-50 p-4 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-300">
            <Inbox className="h-8 w-8" />
          </span>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-200">
            No invoices yet
          </h2>
          <p className="max-w-sm text-sm text-slate-600 dark:text-slate-400">
            Take a photo of a bill or upload a PDF. It will be read, checked,
            and ready to review in under a minute.
          </p>
          <Link to="/upload" className={primaryButton}>
            Upload your first bill
          </Link>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {STATS.map((stat) => (
              <StatCard
                key={stat.key}
                stat={stat}
                value={counts[stat.key]}
                active={filter === stat.key}
                onClick={() =>
                  setFilter(filter === stat.key ? "ALL" : stat.key)
                }
              />
            ))}
          </div>

          {counts.PROCESSING > 0 && (
            <p className="flex items-center gap-2 rounded-xl bg-amber-50 px-4 py-2.5 text-sm text-amber-800 dark:bg-amber-500/10 dark:text-amber-300">
              <Spinner label="Reading" />
              Reading {counts.PROCESSING}{" "}
              {counts.PROCESSING === 1 ? "bill" : "bills"}. This list updates by
              itself.
            </p>
          )}

          <div className="flex flex-col gap-3 sm:flex-row">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search vendor, invoice number or GSTIN"
                className={`${inputClass} pl-9`}
              />
            </div>
            <select
              value={sort}
              onChange={(event) => setSort(event.target.value)}
              aria-label="Sort invoices"
              className={`${inputClass} sm:w-56`}
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.key} value={option.key}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {filtering && (
            <button
              type="button"
              onClick={() => {
                setFilter("ALL");
                setSearch("");
              }}
              className="inline-flex items-center gap-1 rounded-full bg-slate-200 px-3 py-1 text-sm font-medium text-slate-700 hover:bg-slate-300 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              Showing {visible.length} of {data.length}
              <X className="h-3.5 w-3.5" />
            </button>
          )}

          {visible.length === 0 ? (
            <p
              className={`${cardClass} p-6 text-center text-slate-500 dark:text-slate-400`}
            >
              No invoices match your search.
            </p>
          ) : (
            <ul
              className={`${cardClass} divide-y divide-slate-100 overflow-hidden dark:divide-slate-700/70`}
            >
              {visible.map((invoice) => {
                const { icon: RowIcon, tone } =
                  ROW_ICON[invoice.status] ?? ROW_ICON.PROCESSING;
                return (
                  <li key={invoice.id}>
                    <Link
                      to={`/invoices/${invoice.id}`}
                      className="group flex items-center gap-3 px-4 py-3 transition hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-indigo-500 dark:hover:bg-slate-700/70 sm:gap-4"
                    >
                      <span
                        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${tone}`}
                      >
                        <RowIcon className="h-5 w-5" />
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-semibold text-slate-900 dark:text-slate-200">
                          {invoice.vendor_name ?? invoice.original_filename}
                        </p>
                        <p className="truncate text-sm text-slate-500 dark:text-slate-400">
                          {timeAgo(invoice.created_at)}
                          {invoice.invoice_number
                            ? ` · #${invoice.invoice_number}`
                            : ""}
                        </p>
                        <div className="mt-1 flex flex-wrap gap-1.5">
                          <FlagChips invoice={invoice} />
                        </div>
                      </div>
                      <div className="flex shrink-0 flex-col items-end gap-1">
                        <p className="font-semibold text-slate-900 dark:text-slate-200">
                          {formatMoney(invoice.total)}
                        </p>
                        <StatusBadge status={invoice.status} />
                      </div>
                      <ChevronRight className="hidden h-5 w-5 shrink-0 text-slate-300 transition group-hover:text-slate-500 dark:text-slate-600 dark:group-hover:text-slate-300 sm:block" />
                    </Link>

                    {invoice.status === "FAILED" && (
                      <div className="flex flex-wrap items-center gap-3 px-4 pb-3 sm:pl-[4.5rem]">
                        <p className="text-sm text-rose-600 dark:text-rose-400">
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
                          <RefreshCw className="h-4 w-4" />
                          Try again
                        </button>
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </>
      )}
    </div>
  );
}
