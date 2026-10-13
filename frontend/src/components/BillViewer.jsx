import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { fetchInvoiceFile } from "../api/invoices";
import { cardClass } from "../ui";
import { ZoomIn, ZoomOut } from "./icons";
import Skeleton from "./Skeleton";

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

const iconButton =
  "rounded-lg p-2 text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:hover:bg-transparent dark:text-slate-300 dark:hover:bg-slate-800";

export default function BillViewer({ invoiceId }) {
  const [zoom, setZoom] = useState(1);
  const [grabbing, setGrabbing] = useState(false);
  const viewport = useRef(null);
  const drag = useRef(null);

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

  if (isLoading) return <Skeleton className="h-[50vh] w-full rounded-2xl" />;
  if (error || !url) {
    return (
      <div className={`${cardClass} p-6 text-sm text-rose-700`}>
        Could not load the bill image. It may have been removed from the server.
      </div>
    );
  }

  const isPdf = blob.type === "application/pdf";

  // Mouse users can drag a zoomed image around. Touch screens scroll natively.
  function startPan(event) {
    if (event.pointerType !== "mouse" || zoom <= 1) return;
    const box = viewport.current;
    drag.current = {
      x: event.clientX,
      y: event.clientY,
      left: box.scrollLeft,
      top: box.scrollTop,
    };
    setGrabbing(true);
  }
  function movePan(event) {
    if (!drag.current) return;
    const box = viewport.current;
    box.scrollLeft = drag.current.left - (event.clientX - drag.current.x);
    box.scrollTop = drag.current.top - (event.clientY - drag.current.y);
  }
  function endPan() {
    drag.current = null;
    setGrabbing(false);
  }

  return (
    <div className={`${cardClass} p-3`}>
      {!isPdf && (
        <div className="mb-2 flex items-center gap-1">
          <button
            type="button"
            className={iconButton}
            disabled={zoom <= 1}
            onClick={() => setZoom((value) => Math.max(1, value - 0.5))}
            aria-label="Zoom out"
          >
            <ZoomOut className="h-4 w-4" />
          </button>
          <input
            type="range"
            min="1"
            max="4"
            step="0.25"
            value={zoom}
            onChange={(event) => setZoom(Number(event.target.value))}
            aria-label="Zoom"
            className="w-24 accent-indigo-600 sm:w-32"
          />
          <button
            type="button"
            className={iconButton}
            disabled={zoom >= 4}
            onClick={() => setZoom((value) => Math.min(4, value + 0.5))}
            aria-label="Zoom in"
          >
            <ZoomIn className="h-4 w-4" />
          </button>
          <span className="w-12 text-sm text-slate-500 dark:text-slate-400">
            {Math.round(zoom * 100)}%
          </span>
          <button
            type="button"
            className="ml-auto rounded-lg px-2 py-1 text-sm font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
            onClick={() => setZoom(1)}
          >
            Fit
          </button>
          <a
            href={url}
            target="_blank"
            rel="noreferrer"
            className="rounded-lg px-2 py-1 text-sm font-medium text-indigo-600 hover:bg-indigo-50 dark:text-indigo-300 dark:hover:bg-indigo-500/10"
          >
            Open full size
          </a>
        </div>
      )}

      <div
        ref={viewport}
        onPointerDown={startPan}
        onPointerMove={movePan}
        onPointerUp={endPan}
        onPointerLeave={endPan}
        className={`max-h-[50vh] overflow-auto rounded-xl border border-slate-200 bg-slate-100 dark:border-slate-700 dark:bg-slate-900 lg:max-h-[calc(100vh-11rem)] ${
          zoom > 1 ? (grabbing ? "cursor-grabbing" : "cursor-grab") : ""
        }`}
      >
        {isPdf ? (
          <iframe title="Original bill" src={url} className="h-[60vh] w-full" />
        ) : (
          <img
            src={url}
            alt="The original bill"
            draggable={false}
            className="block select-none"
            style={{ width: `${zoom * 100}%`, maxWidth: "none" }}
          />
        )}
      </div>
    </div>
  );
}
