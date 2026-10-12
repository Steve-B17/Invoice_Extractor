import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import FormField from "../components/FormField";
import { useAuth } from "../context/AuthContext";
import { inputClass, primaryButton } from "../ui";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [serverError, setServerError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm();

  async function onSubmit({ email, password }) {
    setServerError("");
    try {
      await login(email, password);
      navigate(location.state?.from?.pathname ?? "/", { replace: true });
    } catch (error) {
      setServerError(errorMessage(error, "Login failed"));
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="w-full max-w-sm space-y-4 rounded-2xl bg-white p-6 shadow"
      >
        <h1 className="text-2xl font-semibold text-slate-900">Log in</h1>

        <FormField label="Email" error={errors.email?.message}>
          <input
            type="email"
            autoComplete="email"
            className={inputClass}
            {...register("email", { required: "Email is required" })}
          />
        </FormField>

        <FormField label="Password" error={errors.password?.message}>
          <input
            type="password"
            autoComplete="current-password"
            className={inputClass}
            {...register("password", { required: "Password is required" })}
          />
        </FormField>

        {serverError && (
          <p
            role="alert"
            className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700"
          >
            {serverError}
          </p>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className={`${primaryButton} w-full`}
        >
          {isSubmitting ? "Logging in…" : "Log in"}
        </button>

        <p className="text-center text-sm text-slate-600">
          No account?{" "}
          <Link
            to="/register"
            className="font-medium text-indigo-600 hover:underline"
          >
            Register
          </Link>
        </p>
      </form>
    </div>
  );
}
