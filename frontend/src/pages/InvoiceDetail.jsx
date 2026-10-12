import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { errorMessage } from "../api/client";
import { getInvoice } from "../api/invoices";
import BillViewer from "../components/BillViewer";
import ReviewForm from "../components/ReviewForm";
import Spinner from "../components/Spinner";
import StatusBadge from "../components/StatusBadge";

export default function InvoiceDetail() {
  const { id } = useParams();
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

  if (isLoading) return <p className="text-slate-500">Loading…</p>;
  if (error) {
    return (
      <div className="space-y-3">
        <p role="alert" className="rounded-lg bg-red-50 px-3 py-2 text-red-700">
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
          {invoice.vendor_name ?? invoice.original_filename}
        </h1>
        <StatusBadge status={invoice.status} />
      </div>

      {invoice.status === "PROCESSING" ? (
        <div className="flex items-center gap-3 rounded-xl bg-white p-6 shadow">
          <Spinner label="Reading the bill" />
          <p className="text-slate-700">
            Reading the bill. This page updates by itself.
          </p>
        </div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="lg:sticky lg:top-4 lg:self-start">
            <BillViewer invoiceId={invoice.id} />
          </div>
          <ReviewForm invoice={invoice} />
        </div>
      )}
    </div>
  );
}
