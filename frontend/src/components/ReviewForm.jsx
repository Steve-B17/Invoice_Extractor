import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useFieldArray, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import {
  reprocessInvoice,
  updateInvoice,
  verifyInvoice,
} from "../api/invoices";
import {
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
import FlagMessages from "./FlagMessages";

function Field({ label, formError, flags, className = "", children }) {
  return (
    <div className={className}>
      <label className="block">
        <span className="mb-1 block text-sm font-medium text-slate-700">
          {label}
        </span>
        {children}
      </label>
      {formError && <p className="mt-1 text-sm text-red-600">{formError}</p>}
      <FlagMessages flags={flags} />
    </div>
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
  const locked = invoice.status === "VERIFIED";
  const cacheKey = ["invoice", String(invoice.id)];

  const [notice, setNotice] = useState("");
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
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
      queryClient.invalidateQueries({ queryKey: ["invoice"] });
      navigate("/");
    },
  });

  const reread = useMutation({
    mutationFn: () => reprocessInvoice(invoice.id),
    onSuccess: (updated) => {
      queryClient.setQueryData(cacheKey, updated); // status is now PROCESSING
      queryClient.invalidateQueries({ queryKey: ["invoices"] });
    },
  });

  const busy = save.isPending || verify.isPending || reread.isPending;

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

  // The "Saved" message disappears by itself
  useEffect(() => {
    if (!notice) return undefined;
    const timer = setTimeout(() => setNotice(""), 4000);
    return () => clearTimeout(timer);
  }, [notice]);

  const onSave = handleSubmit(async (values) => {
    setActionError("");
    setNeedsForce(false);
    try {
      await save.mutateAsync(values);
      setNotice("Saved. The checks were run again.");
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

  function onReread() {
    const sure = window.confirm(
      "Read the bill again? This replaces everything in the form, including edits you have already saved.",
    );
    if (!sure) return;
    setActionError("");
    reread.mutate(undefined, {
      onError: (error) =>
        setActionError(errorMessage(error, "Could not restart processing")),
    });
  }

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
    <form onSubmit={onSave} noValidate className="space-y-5">
      {locked && (
        <p className="rounded-xl bg-green-50 px-4 py-3 text-green-800">
          This invoice is verified and locked.
        </p>
      )}

      {invoice.error_message && !locked && (
        <div className="space-y-2 rounded-xl bg-amber-50 px-4 py-3 text-amber-900">
          <p>{invoice.error_message}</p>
          <button
            type="button"
            className={secondaryButton}
            disabled={busy}
            onClick={onReread}
          >
            Read the bill again
          </button>
        </div>
      )}

      {!locked && (
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          {flagErrors + flagWarnings > 0 ? (
            <>
              <p className="font-medium text-slate-900">
                {[
                  flagErrors > 0 && plural(flagErrors, "error"),
                  flagWarnings > 0 && plural(flagWarnings, "warning"),
                ]
                  .filter(Boolean)
                  .join(" and ")}{" "}
                to check
              </p>
              <p className="text-sm text-slate-600">
                Highlighted fields do not agree with the other numbers on the
                bill. Compare each one with the image, fix what is wrong, and
                save. The highlights refresh when you save.
              </p>
              <FlagMessages flags={general} />
            </>
          ) : (
            <p className="font-medium text-green-700">
              All checks passed. Compare the bill once yourself, then verify.
            </p>
          )}
        </div>
      )}

      <fieldset disabled={locked || busy} className="space-y-6">
        <section className="grid gap-3 sm:grid-cols-2">
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
        </section>

        <section>
          <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Amounts (Rs)
          </h2>
          <div className="grid grid-cols-2 gap-3">
            {moneyField("subtotal", "Subtotal")}
            {moneyField("cgst", "CGST")}
            {moneyField("sgst", "SGST")}
            {moneyField("igst", "IGST")}
            {moneyField("round_off", "Round off")}
            {moneyField("total", "Total")}
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Line items
          </h2>

          {fields.length === 0 && (
            <p className="text-sm text-slate-500">No line items.</p>
          )}

          {fields.map((field, index) => {
            const flags = byItem[index];
            const severity = topSeverity(flags);
            const rowErrors = errors.line_items?.[index] ?? {};
            const tone =
              severity === "error"
                ? "border-red-300 bg-red-50/50"
                : severity === "warning"
                  ? "border-amber-300 bg-amber-50/50"
                  : "border-slate-200";

            return (
              <div key={field.id} className={`rounded-xl border p-3 ${tone}`}>
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-sm font-medium text-slate-700">
                    Item {index + 1}
                  </p>
                  <button
                    type="button"
                    onClick={() => remove(index)}
                    className="text-sm text-red-600 hover:underline"
                  >
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
            Add item
          </button>
        </section>
      </fieldset>

      {isDirty && !locked && (
        <p className="text-sm text-slate-600">You have unsaved changes.</p>
      )}
      {notice && (
        <p className="rounded-lg bg-green-50 px-3 py-2 text-sm text-green-800">
          {notice}
        </p>
      )}
      {actionError && (
        <div
          role="alert"
          className="space-y-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800"
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
        <div className="sticky bottom-0 -mx-4 flex flex-wrap items-center gap-3 border-t bg-white/95 px-4 py-3 backdrop-blur">
          <button
            type="submit"
            className={primaryButton}
            disabled={!isDirty || busy}
          >
            {save.isPending ? "Saving…" : "Save changes"}
          </button>
          <button
            type="button"
            className={secondaryButton}
            disabled={!isDirty || busy}
            onClick={() => reset(toFormValues(invoice))}
          >
            Discard changes
          </button>
          <button
            type="button"
            className={`${successButton} sm:ml-auto`}
            disabled={busy}
            onClick={onVerify}
          >
            {verify.isPending ? "Verifying…" : "Verify"}
          </button>
        </div>
      )}
    </form>
  );
}
