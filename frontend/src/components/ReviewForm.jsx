import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useFieldArray, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { errorMessage } from "../api/client";
import {
  reprocessInvoice,
  updateInvoice,
  verifyInvoice,
} from "../api/invoices";
import {
  cardClass,
  fieldClass,
  inputClass,
  primaryButton,
  secondaryButton,
  successButton,
} from "../ui";
import { countSeverities, groupFlags, topSeverity } from "../utils/flags";
import {
  isMoney,
  isQuantity,
  toFormValues,
  toPayload,
} from "../utils/invoiceForm";
import { nextToReview } from "../utils/invoiceStats";
import { useConfirm } from "./ConfirmProvider";
import FlagMessages from "./FlagMessages";
import {
  Plus,
  RefreshCw,
  Save,
  ShieldCheck,
  Trash2,
  TriangleAlert,
  Undo2,
} from "./icons";

function Field({ label, formError, flags, className = "", children }) {
  return (
    <div className={className}>
      <label className="block">
        <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
          {label}
        </span>
        {children}
      </label>
      {formError && <p className="mt-1 text-sm text-rose-600 dark:text-rose-400">{formError}</p>}
      <FlagMessages flags={flags} />
    </div>
  );
}

function Section({ title, hint, children }) {
  return (
    <section className={`${cardClass} p-4 sm:p-5`}>
      <div className="mb-3">
        <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-200">{title}</h2>
        {hint && <p className="text-sm text-slate-500 dark:text-slate-400">{hint}</p>}
      </div>
      {children}
    </section>
  );
}

const moneyRule = {
  validate: (value) => isMoney(value) || "Use a number such as 123.45",
};
const quantityRule = {
  validate: (value) => isQuantity(value) || "Use a number such as 2 or 1.5",
};
const EMPTY_ITEM = {
  description: "",
  hsn_code: "",
  quantity: "",
  rate: "",
  amount: "",
};

function plural(count, word) {
  return `${count} ${word}${count === 1 ? "" : "s"}`;
}

export default function ReviewForm({ invoice }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const confirm = useConfirm();
  const locked = invoice.status === "VERIFIED";
  const cacheKey = ["invoice", String(invoice.id)];

  const [needsForce, setNeedsForce] = useState(false);
  const [actionError, setActionError] = useState("");

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm({ defaultValues: toFormValues(invoice) });
  const { fields, append, remove } = useFieldArray({
    control,
    name: "line_items",
  });

  const { byField, byItem, general } = groupFlags(invoice.flags);
  const { errors: flagErrors, warnings: flagWarnings } = countSeverities(
    invoice.flags,
  );

  const save = useMutation({
    mutationFn: (values) => updateInvoice(invoice.id, toPayload(values)),
    onSuccess: (updated) => {
      queryClient.setQueryData(cacheKey, updated); // the response already carries the new flags
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      reset(toFormValues(updated)); // shows the values as the server normalised them
    },
  });

  const verify = useMutation({
    mutationFn: (force) => verifyInvoice(invoice.id, force),
    onSuccess: () => {
      // pick the next bill waiting for review from the list we already have
      const next = nextToReview(
        queryClient.getQueryData(["invoices"]),
        invoice.id,
      );
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: ["invoice"] });
      if (next) {
        toast.success("Verified", {
          description: "Opening the next bill to review.",
        });
        navigate(`/invoices/${next.id}`);
      } else {
        toast.success("Verified. You are all caught up.");
        navigate("/");
      }
    },
  });

  const reread = useMutation({
    mutationFn: () => reprocessInvoice(invoice.id),
    onSuccess: (updated) => {
      queryClient.setQueryData(cacheKey, updated); // status is now PROCESSING
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      toast.success("Reading the bill again");
    },
    onError: (error) =>
      setActionError(errorMessage(error, "Could not restart processing")),
  });

  const busy = save.isPending || verify.isPending || reread.isPending;

  const onSave = handleSubmit(async (values) => {
    setActionError("");
    setNeedsForce(false);
    try {
      await save.mutateAsync(values);
      toast.success("Saved. The checks were run again.");
    } catch (error) {
      setActionError(errorMessage(error, "Could not save"));
    }
  });

  async function runVerify(values, force) {
    setActionError("");
    setNeedsForce(false);
    try {
      if (isDirty) await save.mutateAsync(values); // never verify numbers nobody has saved
      await verify.mutateAsync(force);
    } catch (error) {
      const message = errorMessage(error, "Could not verify this invoice");
      setActionError(message);
      setNeedsForce(
        error.response?.status === 409 && /validation error/i.test(message),
      );
    }
  }

  const onVerify = handleSubmit((values) => runVerify(values, false));
  const onVerifyAnyway = handleSubmit((values) => runVerify(values, true));

  async function onReread() {
    const sure = await confirm({
      title: "Read the bill again?",
      message:
        "This replaces everything in the form, including edits you have already saved.",
      confirmLabel: "Read again",
      tone: "danger",
    });
    if (!sure) return;
    setActionError("");
    reread.mutate();
  }

  // Warn before the tab is closed with unsaved edits
  useEffect(() => {
    if (!isDirty) return undefined;
    const warn = (event) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [isDirty]);

  // Ctrl+S (or Cmd+S) saves
  useEffect(() => {
    function onKeyDown(event) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        if (isDirty && !busy && !locked) onSave();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  function textField(name, label, props = {}, className = "") {
    return (
      <Field
        label={label}
        formError={errors[name]?.message}
        flags={byField[name]}
        className={className}
      >
        <input
          type="text"
          autoComplete="off"
          className={fieldClass(topSeverity(byField[name]))}
          {...props}
          {...register(name)}
        />
      </Field>
    );
  }

  function moneyField(name, label) {
    return (
      <Field
        key={name}
        label={label}
        formError={errors[name]?.message}
        flags={byField[name]}
      >
        <input
          inputMode="decimal"
          autoComplete="off"
          className={fieldClass(topSeverity(byField[name]))}
          {...register(name, moneyRule)}
        />
      </Field>
    );
  }

  return (
    <form onSubmit={onSave} noValidate className="space-y-4">
      {locked && (
        <div className="flex items-center gap-3 rounded-2xl bg-emerald-50 px-4 py-3 text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-300">
          <ShieldCheck className="h-5 w-5 shrink-0" />
          <p className="font-medium">This invoice is verified and locked.</p>
        </div>
      )}

      {invoice.error_message && !locked && (
        <div className="space-y-3 rounded-2xl bg-amber-50 px-4 py-3 text-amber-900 dark:bg-amber-500/10 dark:text-amber-300">
          <p className="text-sm">{invoice.error_message}</p>
          <button
            type="button"
            className={secondaryButton}
            disabled={busy}
            onClick={onReread}
          >
            <RefreshCw className="h-4 w-4" />
            Read the bill again
          </button>
        </div>
      )}

      {!locked && (
        <div className={`${cardClass} p-4 sm:p-5`}>
          {flagErrors + flagWarnings > 0 ? (
            <div className="flex items-start gap-3">
              <span className="rounded-xl bg-amber-50 p-2 text-amber-600">
                <TriangleAlert className="h-5 w-5" />
              </span>
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-semibold text-slate-900 dark:text-slate-200">
                    Please check the highlighted fields
                  </p>
                  {flagErrors > 0 && (
                    <span className="rounded-full bg-rose-50 px-2 py-0.5 text-xs font-medium text-rose-700 ring-1 ring-inset ring-rose-200">
                      {plural(flagErrors, "error")}
                    </span>
                  )}
                  {flagWarnings > 0 && (
                    <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-200">
                      {plural(flagWarnings, "warning")}
                    </span>
                  )}
                </div>
                <p className="text-sm text-slate-600 dark:text-slate-300">
                  Highlighted fields do not agree with the other numbers on the
                  bill. Compare each one with the image, fix what is wrong, and
                  save. The highlights refresh when you save.
                </p>
                <FlagMessages flags={general} />
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <span className="rounded-xl bg-emerald-50 p-2 text-emerald-600">
                <ShieldCheck className="h-5 w-5" />
              </span>
              <p className="font-semibold text-emerald-700">
                All checks passed. Compare the bill once yourself, then verify.
              </p>
            </div>
          )}
        </div>
      )}

      <fieldset disabled={locked || busy} className="min-w-0 space-y-4">
        <Section title="Vendor and bill">
          <div className="grid gap-3 sm:grid-cols-2">
            {textField(
              "vendor_name",
              "Vendor",
              { maxLength: 255 },
              "sm:col-span-2",
            )}
            {textField("gstin", "GSTIN (15 characters)", {
              maxLength: 15,
              autoCapitalize: "characters",
              spellCheck: false,
            })}
            {textField("invoice_number", "Invoice number", { maxLength: 100 })}
            {textField("invoice_date", "Date", { type: "date" })}
          </div>
        </Section>

        <Section title="Amounts" hint="All amounts in rupees.">
          <div className="grid grid-cols-2 gap-3">
            {moneyField("subtotal", "Subtotal")}
            {moneyField("cgst", "CGST")}
            {moneyField("sgst", "SGST")}
            {moneyField("igst", "IGST")}
            {moneyField("round_off", "Round off")}
            {moneyField("total", "Total")}
          </div>
        </Section>

        <Section title="Line items">
          <div className="space-y-3">
            {fields.length === 0 && (
              <p className="text-sm text-slate-500 dark:text-slate-400">No line items.</p>
            )}

            {fields.map((field, index) => {
              const flags = byItem[index];
              const severity = topSeverity(flags);
              const rowErrors = errors.line_items?.[index] ?? {};
              const tone =
                severity === "error"
                  ? "border-rose-300 bg-rose-50/50 dark:border-rose-500/40 dark:bg-rose-500/5"
                  : severity === "warning"
                    ? "border-amber-300 bg-amber-50/50 dark:border-amber-500/40 dark:bg-amber-500/5"
                    : "border-slate-200 dark:border-slate-700/80 dark:bg-slate-800/70";

              return (
                <div key={field.id} className={`rounded-xl border p-3 ${tone}`}>
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                      Item {index + 1}
                    </p>
                    <button
                      type="button"
                      onClick={() => remove(index)}
                      className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-sm text-rose-600 hover:bg-rose-50 dark:text-rose-300 dark:hover:bg-rose-500/10"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Remove
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                    <Field
                      label="Description"
                      className="col-span-2 sm:col-span-4"
                    >
                      <input
                        type="text"
                        maxLength={255}
                        className={inputClass}
                        {...register(`line_items.${index}.description`)}
                      />
                    </Field>
                    <Field label="HSN code">
                      <input
                        type="text"
                        maxLength={20}
                        className={inputClass}
                        {...register(`line_items.${index}.hsn_code`)}
                      />
                    </Field>
                    <Field
                      label="Quantity"
                      formError={rowErrors.quantity?.message}
                    >
                      <input
                        inputMode="decimal"
                        className={inputClass}
                        {...register(
                          `line_items.${index}.quantity`,
                          quantityRule,
                        )}
                      />
                    </Field>
                    <Field label="Rate" formError={rowErrors.rate?.message}>
                      <input
                        inputMode="decimal"
                        className={inputClass}
                        {...register(`line_items.${index}.rate`, moneyRule)}
                      />
                    </Field>
                    <Field label="Amount" formError={rowErrors.amount?.message}>
                      <input
                        inputMode="decimal"
                        className={inputClass}
                        {...register(`line_items.${index}.amount`, moneyRule)}
                      />
                    </Field>
                  </div>

                  <FlagMessages flags={flags} />
                </div>
              );
            })}

            <button
              type="button"
              className={secondaryButton}
              onClick={() => append({ ...EMPTY_ITEM })}
            >
              <Plus className="h-4 w-4" />
              Add item
            </button>
          </div>
        </Section>
      </fieldset>

      {actionError && (
        <div
          role="alert"
          className="space-y-2 rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-800"
        >
          <p>{actionError}</p>
          {needsForce && (
            <button
              type="button"
              className={secondaryButton}
              disabled={busy}
              onClick={onVerifyAnyway}
            >
              I checked the bill. Verify anyway
            </button>
          )}
        </div>
      )}

      {!locked && (
        <div className="sticky bottom-3 z-10 flex flex-wrap items-center gap-2 rounded-2xl border border-slate-200 bg-white/95 p-3 shadow-lg backdrop-blur dark:border-slate-700/80 dark:bg-slate-800/90">
          <button
            type="submit"
            className={primaryButton}
            disabled={!isDirty || busy}
            title="Save (Ctrl+S)"
          >
            <Save className="h-4 w-4" />
            {save.isPending ? "Saving…" : "Save"}
          </button>
          <button
            type="button"
            className={secondaryButton}
            disabled={!isDirty || busy}
            onClick={() => reset(toFormValues(invoice))}
          >
            <Undo2 className="h-4 w-4" />
            Discard
          </button>
          {isDirty && (
            <span className="text-sm text-slate-500 dark:text-slate-400">Unsaved changes</span>
          )}
          <button
            type="button"
            className={`${successButton} ml-auto`}
            disabled={busy}
            onClick={onVerify}
          >
            <ShieldCheck className="h-4 w-4" />
            {verify.isPending ? "Verifying…" : "Verify & next"}
          </button>
        </div>
      )}
    </form>
  );
}
