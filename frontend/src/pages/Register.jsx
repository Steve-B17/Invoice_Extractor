import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import FormField from "../components/FormField";
import { useAuth } from "../context/AuthContext";
import { inputClass, primaryButton } from "../ui";

export default function Register() {
  const { register: signUp } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState("");
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm();

  async function onSubmit({ email, password }) {
    setServerError("");
    try {
      await signUp(email, password);
      navigate("/", { replace: true });
    } catch (error) {
      setServerError(errorMessage(error, "Registration failed"));
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="w-full max-w-sm space-y-4 rounded-2xl bg-white p-6 shadow"
      >
        <h1 className="text-2xl font-semibold text-slate-900">
          Create an account
        </h1>

        <FormField label="Email" error={errors.email?.message}>
          <input
            type="email"
            autoComplete="email"
            className={inputClass}
            {...register("email", { required: "Email is required" })}
          />
        </FormField>

        <FormField
          label="Password (8 to 72 characters)"
          error={errors.password?.message}
        >
          <input
            type="password"
            autoComplete="new-password"
            className={inputClass}
            {...register("password", {
              required: "Password is required",
              minLength: { value: 8, message: "Use at least 8 characters" },
              maxLength: { value: 72, message: "Use at most 72 characters" },
            })}
          />
        </FormField>

        <FormField label="Confirm password" error={errors.confirm?.message}>
          <input
            type="password"
            autoComplete="new-password"
            className={inputClass}
            {...register("confirm", {
              required: "Please repeat the password",
              validate: (value) =>
                value === watch("password") || "Passwords do not match",
            })}
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
          {isSubmitting ? "Creating account…" : "Register"}
        </button>

        <p className="text-center text-sm text-slate-600">
          Already registered?{" "}
          <Link
            to="/login"
            className="font-medium text-indigo-600 hover:underline"
          >
            Log in
          </Link>
        </p>
      </form>
    </div>
  );
}
