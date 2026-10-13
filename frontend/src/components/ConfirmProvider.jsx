import {
  createContext,
  useCallback,
  useContext,
  useRef,
  useState,
} from "react";
import { dangerButton, primaryButton, secondaryButton } from "../ui";

const ConfirmContext = createContext(null);

export function ConfirmProvider({ children }) {
  const dialog = useRef(null);
  const resolver = useRef(null);
  const [options, setOptions] = useState({ title: "", message: "" });

  // confirm({ title, message, confirmLabel, tone }) returns a promise: true or false
  const confirm = useCallback(
    (next) =>
      new Promise((resolve) => {
        resolver.current = resolve;
        setOptions(next);
        dialog.current?.showModal();
      }),
    [],
  );

  function finish(result) {
    dialog.current?.close();
    resolver.current?.(result);
    resolver.current = null;
  }

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      <dialog
        ref={dialog}
        onCancel={(event) => {
          event.preventDefault(); // Escape key
          finish(false);
        }}
        onClick={(event) => {
          if (event.target === dialog.current) finish(false); // click on the dark backdrop
        }}
        className="m-auto w-[calc(100%-2rem)] max-w-md rounded-2xl border border-slate-200 bg-white p-0 shadow-xl backdrop:bg-slate-900/40 backdrop:backdrop-blur-sm dark:border-slate-700/80 dark:bg-slate-800"
      >
        <div className="space-y-4 p-6">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-200">
            {options.title}
          </h2>
          <p className="text-sm text-slate-600 dark:text-slate-300">{options.message}</p>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              className={secondaryButton}
              onClick={() => finish(false)}
            >
              Cancel
            </button>
            <button
              type="button"
              className={
                options.tone === "danger" ? dangerButton : primaryButton
              }
              onClick={() => finish(true)}
            >
              {options.confirmLabel ?? "Confirm"}
            </button>
          </div>
        </div>
      </dialog>
    </ConfirmContext.Provider>
  );
}

export function useConfirm() {
  const confirm = useContext(ConfirmContext);
  if (!confirm)
    throw new Error("useConfirm must be used inside <ConfirmProvider>");
  return confirm;
}
