import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { errorMessage } from "../api/client";
import { deleteInvoice, getInvoice } from "../api/invoices";
import BillViewer from "../components/BillViewer";
import { useConfirm } from "../components/ConfirmProvider";
import { ArrowLeft, Trash2 } from "../components/icons";
import ReviewForm from "../components/ReviewForm";
import Skeleton from "../components/Skeleton";
import Spinner from "../components/Spinner";
import StatusBadge from "../components/StatusBadge";
import useDocumentTitle from "../hooks/useDocumentTitle";
import { cardClass } from "../ui";
import { timeAgo } from "../utils/invoiceStats";

export default function InvoiceDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const confirm = useConfirm();
  const [tab, setTab] = useState("details"); // phones show one panel at a time

  const {
    data: invoice,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["invoice", id],
    queryFn: () => getInvoice(id),
    // while the bill is being read, check every 3 seconds
    refetchInterval: (query) =>
      query.state.data?.status === "PROCESSING" ? 3000 : false,
  });

  useDocumentTitle(
    invoice ? (invoice.vendor_name ?? invoice.original_filename) : "Invoice",
  );

  const remove = useMutation({
    mutationFn: () => deleteInvoice(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      toast.success("Invoice deleted");
      navigate("/");
    },
    onError: (failure) =>
      toast.error(errorMessage(failure, "Could not delete this invoice")),
  });

  async function onDelete() {
    const sure = await confirm({
      title: "Delete this invoice?",
      message:
        "The extracted data and the stored bill image will be removed. This cannot be undone.",
      confirmLabel: "Delete",
      tone: "danger",
    });
    if (sure) remove.mutate();
  }

  if (isLoading) {
    return (
      <div className="space-y-5">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-8 w-1/2" />
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-[50vh] rounded-2xl" />
          <Skeleton className="h-[50vh] rounded-2xl" />
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div className="space-y-3">
        <p
          role="alert"
          className="rounded-xl bg-rose-50 px-4 py-3 text-rose-700"
        >
          {errorMessage(error, "Could not load this invoice")}
        </p>
        <Link
          to="/"
          className="text-sm font-medium text-indigo-600 hover:underline"
        >
          ← Back to invoices
        </Link>
      </div>
    );
  }

  const problems = (invoice.flags ?? []).length;

  return (
    <div className="space-y-5">
      <Link
        to="/"
        className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:underline"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to invoices
      </Link>

      <div className="space-y-1">
        <div className="flex items-center justify-between gap-3">
          <h1 className="truncate text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-200">
            {invoice.vendor_name ?? invoice.original_filename}
          </h1>
          <div className="flex shrink-0 items-center gap-2">
            <StatusBadge status={invoice.status} />
            <button
              type="button"
              onClick={onDelete}
              disabled={remove.isPending || invoice.status === "PROCESSING"}
              className="rounded-lg p-2 text-slate-500 hover:bg-rose-50 hover:text-rose-600 disabled:opacity-50 dark:text-slate-300 dark:hover:bg-rose-500/10 dark:hover:text-rose-300"
              aria-label="Delete invoice"
              title="Delete invoice"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
        </div>
        <p className="truncate text-sm text-slate-500 dark:text-slate-400">
          Uploaded {timeAgo(invoice.created_at)} · {invoice.original_filename}
          {invoice.confidence != null
            ? ` · reading quality ${Math.round(invoice.confidence * 100)}%`
            : ""}
        </p>
      </div>

      {invoice.status === "PROCESSING" ? (
        <div className={`${cardClass} flex items-center gap-3 p-6`}>
          <Spinner label="Reading the bill" />
          <p className="text-slate-700 dark:text-slate-300">
            Reading the bill. This page updates by itself.
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-1 rounded-xl bg-slate-200/70 p-1 dark:bg-slate-700/70 lg:hidden">
            {[
              {
                key: "details",
                label: problems > 0 ? `Details (${problems})` : "Details",
              },
              { key: "bill", label: "Bill image" },
            ].map(({ key, label }) => (
              <button
                key={key}
                type="button"
                onClick={() => setTab(key)}
                className={`rounded-lg py-1.5 text-sm font-medium transition ${
                  tab === key
                    ? "bg-white text-slate-900 shadow-sm dark:bg-slate-600 dark:text-slate-200"
                    : "text-slate-600 dark:text-slate-300"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <div
              className={`${tab === "bill" ? "block" : "hidden"} lg:sticky lg:top-20 lg:block lg:self-start`}
            >
              <BillViewer invoiceId={invoice.id} />
            </div>
            <div
              className={`${tab === "details" ? "block" : "hidden"} min-w-0 lg:block`}
            >
              <ReviewForm invoice={invoice} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}
