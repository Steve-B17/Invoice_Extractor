import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { errorMessage } from "../api/client";
import { uploadInvoice } from "../api/invoices";
import {
  Camera,
  Check,
  FileText,
  FolderOpen,
  UploadIcon,
  X,
} from "../components/icons";
import Spinner from "../components/Spinner";
import useDocumentTitle from "../hooks/useDocumentTitle";
import { cardClass, primaryButton, secondaryButton } from "../ui";
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
  useDocumentTitle("Upload");
  const queryClient = useQueryClient();
  const nextId = useRef(1); // a counter works everywhere, unlike crypto.randomUUID on plain http
  const previews = useRef(new Set());
  const [items, setItems] = useState([]);
  const [dragging, setDragging] = useState(false);

  // release the temporary thumbnail URLs when leaving the page
  useEffect(() => {
    const urls = previews.current;
    return () => {
      urls.forEach((url) => URL.revokeObjectURL(url));
      urls.clear();
    };
  }, []);

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
      return true;
    } catch (error) {
      const message = error.isAxiosError
        ? errorMessage(error, "Upload failed")
        : error.message;
      patch(item.id, { status: "error", message });
      return false;
    }
  }

  async function handleFiles(fileList) {
    const added = Array.from(fileList).map((file) => {
      const preview = file.type.startsWith("image/")
        ? URL.createObjectURL(file)
        : null;
      if (preview) previews.current.add(preview);
      return {
        id: nextId.current++,
        file,
        name: file.name,
        preview,
        status: "waiting",
        progress: 0,
        message: "",
      };
    });
    if (added.length === 0) return;

    setItems((current) => [...added, ...current]);
    let succeeded = 0;
    for (const item of added) {
      if (await processFile(item)) succeeded += 1; // one at a time, so the server is not flooded
    }
    queryClient.invalidateQueries({ queryKey: ["invoices"] });
    if (succeeded > 0) {
      toast.success(
        succeeded === 1
          ? "Bill uploaded. Reading it now."
          : `${succeeded} bills uploaded. Reading them now.`,
      );
    }
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

  function clearList() {
    previews.current.forEach((url) => URL.revokeObjectURL(url));
    previews.current.clear();
    setItems([]);
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-200">
        Upload bills
      </h1>

      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`rounded-3xl border-2 border-dashed p-6 text-center transition sm:p-10 ${
          dragging
            ? "scale-[1.01] border-indigo-500 bg-indigo-50 dark:bg-indigo-500/10"
            : "border-slate-300 bg-white dark:border-slate-700 dark:bg-slate-800"
        }`}
      >
        <span className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
          <UploadIcon className="h-7 w-7" />
        </span>
        <p className="font-semibold text-slate-900 dark:text-slate-200">
          {dragging
            ? "Drop the files to upload"
            : "Take a photo of a bill, or choose files"}
        </p>
        <p className="mb-6 mt-1 text-sm text-slate-500 dark:text-slate-400">
          JPG, PNG, WebP or PDF, up to 10 MB each. You can also drag files here.
        </p>

        <div className="flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center">
          <label
            className={`${primaryButton} cursor-pointer py-2.5 focus-within:ring-2 focus-within:ring-indigo-300`}
          >
            <Camera className="h-4 w-4" />
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
            className={`${secondaryButton} cursor-pointer py-2.5 focus-within:ring-2 focus-within:ring-indigo-300`}
          >
            <FolderOpen className="h-4 w-4" />
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

        <p className="mt-5 text-xs text-slate-500 dark:text-slate-400">
          Tip: lay the bill flat in even light, with the whole bill in the
          frame.
        </p>
      </div>

      {items.length > 0 && (
        <ul
          className={`${cardClass} divide-y divide-slate-100 overflow-hidden`}
        >
          {items.map((item) => (
            <li key={item.id} className="flex items-center gap-3 p-3 sm:p-4">
              <div className="h-12 w-12 shrink-0 overflow-hidden rounded-xl bg-slate-100 dark:bg-slate-800">
                {item.preview ? (
                  <img
                    src={item.preview}
                    alt=""
                    className="h-full w-full object-cover"
                    onError={(event) => {
                      event.currentTarget.style.display = "none";
                    }}
                  />
                ) : (
                      <div className="flex h-full w-full items-center justify-center text-slate-400 dark:text-slate-500">
                    <FileText className="h-6 w-6" />
                  </div>
                )}
              </div>

              <div className="min-w-0 flex-1 space-y-1">
                    <p className="truncate text-sm font-semibold text-slate-900 dark:text-slate-200">
                  {item.name}
                </p>
                {item.status === "error" ? (
                      <p role="alert" className="text-sm text-rose-700 dark:text-rose-300">
                    {item.message}
                  </p>
                ) : (
                      <p className="text-sm text-slate-500 dark:text-slate-400">
                    {STATUS_TEXT[item.status]}
                  </p>
                )}
                {item.status === "uploading" && (
                      <div className="h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                    <div
                      className="h-full rounded-full bg-indigo-600 transition-all"
                      style={{ width: `${item.progress}%` }}
                    />
                  </div>
                )}
              </div>

              <div className="shrink-0">
                {(item.status === "preparing" ||
                  item.status === "uploading") && <Spinner label="Working" />}
                {item.status === "done" && (
                  <Link
                    to={`/invoices/${item.invoiceId}`}
                    className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-100"
                  >
                    <Check className="h-3.5 w-3.5" />
                    Open
                  </Link>
                )}
                {item.status === "error" && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-1 text-xs font-medium text-rose-700">
                    <X className="h-3.5 w-3.5" />
                    Failed
                  </span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="flex flex-wrap gap-3">
        <Link to="/" className={primaryButton}>
          View invoices
        </Link>
        {finished && !busy && (
          <button type="button" className={secondaryButton} onClick={clearList}>
            Clear list
          </button>
        )}
      </div>
    </div>
  );
}
