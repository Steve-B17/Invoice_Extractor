import { useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { errorMessage } from "../api/client";
import { uploadInvoice } from "../api/invoices";
import { primaryButton, secondaryButton } from "../ui";
import { prepareFile } from "../utils/prepareFile";

const STATUS_TEXT = {
  waiting: "Waiting…",
  preparing: "Preparing…",
  uploading: "Uploading…",
  done: "Uploaded. The bill is being read.",
};

const ACCEPT_FILES =
  "image/jpeg,image/png,image/webp,application/pdf,.jpg,.jpeg,.png,.webp,.pdf";

export default function Upload() {
  const queryClient = useQueryClient();
  const nextId = useRef(1); // a counter works everywhere, unlike crypto.randomUUID on plain http
  const [items, setItems] = useState([]);
  const [dragging, setDragging] = useState(false);

  const busy = items.some((item) =>
    ["waiting", "preparing", "uploading"].includes(item.status),
  );
  const finished = items.some(
    (item) => item.status === "done" || item.status === "error",
  );

  function patch(id, changes) {
    setItems((current) =>
      current.map((item) => (item.id === id ? { ...item, ...changes } : item)),
    );
  }

  async function processFile(item) {
    try {
      patch(item.id, { status: "preparing" });
      const prepared = await prepareFile(item.file);
      patch(item.id, { status: "uploading", progress: 0 });
      const invoice = await uploadInvoice(prepared, (progress) =>
        patch(item.id, { progress }),
      );
      patch(item.id, { status: "done", progress: 100, invoiceId: invoice.id });
    } catch (error) {
      const message = error.isAxiosError
        ? errorMessage(error, "Upload failed")
        : error.message;
      patch(item.id, { status: "error", message });
    }
  }

  async function handleFiles(fileList) {
    const added = Array.from(fileList).map((file) => ({
      id: nextId.current++,
      file,
      name: file.name,
      status: "waiting",
      progress: 0,
      message: "",
    }));
    if (added.length === 0) return;

    setItems((current) => [...added, ...current]);
    for (const item of added) {
      await processFile(item); // one at a time, so the server is not flooded
    }
    queryClient.invalidateQueries({ queryKey: ["invoices"] });
  }

  function onPick(event) {
    handleFiles(event.target.files);
    event.target.value = ""; // lets the same file be chosen again
  }

  function onDrop(event) {
    event.preventDefault();
    setDragging(false);
    handleFiles(event.dataTransfer.files);
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-slate-900">Upload bills</h1>

      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`rounded-2xl border-2 border-dashed p-6 text-center sm:p-10 ${
          dragging
            ? "border-indigo-500 bg-indigo-50"
            : "border-slate-300 bg-white"
        }`}
      >
        <p className="mb-1 text-slate-700">
          Take a photo of a bill, or choose files.
        </p>
        <p className="mb-5 text-sm text-slate-500">
          JPG, PNG, WebP or PDF, up to 10 MB each. You can also drop files here.
        </p>

        <div className="flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center">
          <label
            className={`${primaryButton} cursor-pointer focus-within:ring-2 focus-within:ring-indigo-300`}
          >
            Take photo
            <input
              type="file"
              accept="image/*"
              capture="environment"
              className="sr-only"
              onChange={onPick}
            />
          </label>
          <label
            className={`${secondaryButton} cursor-pointer focus-within:ring-2 focus-within:ring-indigo-300`}
          >
            Choose files
            <input
              type="file"
              multiple
              accept={ACCEPT_FILES}
              className="sr-only"
              onChange={onPick}
            />
          </label>
        </div>

        <p className="mt-4 text-xs text-slate-500">
          Tip: lay the bill flat in even light, with the whole bill in the
          frame.
        </p>
      </div>

      {items.length > 0 && (
        <ul className="divide-y rounded-xl bg-white shadow">
          {items.map((item) => (
            <li key={item.id} className="space-y-2 px-4 py-3">
              <div className="flex items-center justify-between gap-3">
                <p className="truncate font-medium text-slate-900">
                  {item.name}
                </p>
                {item.status === "done" && (
                  <span className="text-sm text-green-700">Uploaded</span>
                )}
                {item.status === "error" && (
                  <span className="text-sm text-red-700">Failed</span>
                )}
              </div>

              {item.status === "error" ? (
                <p role="alert" className="text-sm text-red-700">
                  {item.message}
                </p>
              ) : (
                <>
                  <p className="text-sm text-slate-500">
                    {STATUS_TEXT[item.status]}
                  </p>
                  {item.status === "uploading" && (
                    <div className="h-2 rounded bg-slate-200">
                      <div
                        className="h-2 rounded bg-indigo-600 transition-all"
                        style={{ width: `${item.progress}%` }}
                      />
                    </div>
                  )}
                </>
              )}
            </li>
          ))}
        </ul>
      )}

      <div className="flex flex-wrap gap-3">
        <Link to="/" className={primaryButton}>
          View invoices
        </Link>
        {finished && !busy && (
          <button
            type="button"
            className={secondaryButton}
            onClick={() => setItems([])}
          >
            Clear list
          </button>
        )}
      </div>
    </div>
  );
}
