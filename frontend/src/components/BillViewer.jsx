import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { fetchInvoiceFile } from "../api/invoices";

// A Blob needs a temporary URL to be shown. It must be released when no longer needed.
function useObjectUrl(blob) {
  const [url, setUrl] = useState(null);
  useEffect(() => {
    if (!blob) {
      setUrl(null);
      return undefined;
    }
    const objectUrl = URL.createObjectURL(blob);
    setUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [blob]);
  return url;
}

const ZOOM_STEPS = [1, 1.5, 2, 3, 4];

export default function BillViewer({ invoiceId }) {
  const [zoomIndex, setZoomIndex] = useState(0);

  const {
    data: blob,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["invoice-file", String(invoiceId)],
    queryFn: () => fetchInvoiceFile(invoiceId),
    staleTime: Infinity, // the stored file never changes
  });
  const url = useObjectUrl(blob);

  if (isLoading) {
    return (
      <div className="rounded-xl bg-white p-6 text-slate-500 shadow">
        Loading the bill…
      </div>
    );
  }
  if (error || !url) {
    return (
      <div className="rounded-xl bg-white p-6 text-red-700 shadow">
        Could not load the bill image.
      </div>
    );
  }

  const isPdf = blob.type === "application/pdf";
  const zoom = ZOOM_STEPS[zoomIndex];
  const buttonClass =
    "rounded-md border border-slate-300 px-2.5 py-1 text-sm font-medium text-slate-700 " +
    "hover:bg-slate-50 disabled:opacity-40";

  return (
    <div className="rounded-xl bg-white p-3 shadow">
      {!isPdf && (
        <div className="mb-2 flex items-center gap-2">
          <button
            type="button"
            className={buttonClass}
            disabled={zoomIndex === 0}
            onClick={() => setZoomIndex((index) => index - 1)}
            aria-label="Zoom out"
          >
            −
          </button>
          <span className="w-12 text-center text-sm text-slate-600">
            {Math.round(zoom * 100)}%
          </span>
          <button
            type="button"
            className={buttonClass}
            disabled={zoomIndex === ZOOM_STEPS.length - 1}
            onClick={() => setZoomIndex((index) => index + 1)}
            aria-label="Zoom in"
          >
            +
          </button>
          <span className="ml-2 text-xs text-slate-500">
            Zoom in to read small print and Tamil text.
          </span>
        </div>
      )}

      <div className="max-h-[45vh] overflow-auto rounded-lg border bg-slate-100 lg:max-h-[calc(100vh-9rem)]">
        {isPdf ? (
          <iframe title="Original bill" src={url} className="h-[60vh] w-full" />
        ) : (
          <img
            src={url}
            alt="The original bill"
            className="block"
            style={{ width: `${zoom * 100}%`, maxWidth: "none" }}
          />
        )}
      </div>
    </div>
  );
}
