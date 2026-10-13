import { forwardRef, useState } from "react";
import { inputClass } from "../ui";
import { Eye, EyeOff } from "./icons";

const PasswordInput = forwardRef(function PasswordInput(props, ref) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="relative">
      <input
        ref={ref}
        type={visible ? "text" : "password"}
        className={`${inputClass} pr-11`}
        {...props}
      />
      <button
        type="button"
        onClick={() => setVisible((value) => !value)}
        aria-label={visible ? "Hide password" : "Show password"}
        className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
      >
        {visible ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
      </button>
    </div>
  );
});

export default PasswordInput;
