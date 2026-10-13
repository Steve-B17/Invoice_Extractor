import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import AuthLayout from "../components/AuthLayout";
import FormField from "../components/FormField";
import PasswordInput from "../components/PasswordInput";
import { useAuth } from "../context/AuthContext";
import useDocumentTitle from "../hooks/useDocumentTitle";
import { inputClass, primaryButton } from "../ui";

export default function Login() {
  useDocumentTitle("Log in");
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
    <AuthLayout
      title="Welcome back"
      subtitle="Log in to review your bills."
      footer={
        <>
          No account?{" "}
          <Link
            to="/register"
            className="font-semibold text-indigo-600 hover:underline dark:text-indigo-400"
          >
            Register
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <FormField label="Email" error={errors.email?.message}>
          <input
            type="email"
            autoComplete="email"
            className={inputClass}
            {...register("email", { required: "Email is required" })}
          />
        </FormField>

        <FormField label="Password" error={errors.password?.message}>
          <PasswordInput
            autoComplete="current-password"
            {...register("password", { required: "Password is required" })}
          />
        </FormField>

        {serverError && (
          <p
            role="alert"
            className="rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:bg-rose-950/50 dark:text-rose-300"
          >
            {serverError}
          </p>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className={`${primaryButton} w-full py-2.5`}
        >
          {isSubmitting ? "Logging in…" : "Log in"}
        </button>
      </form>
    </AuthLayout>
  );
}
