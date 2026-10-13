import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import AuthLayout from "../components/AuthLayout";
import FormField from "../components/FormField";
import PasswordInput from "../components/PasswordInput";
import { useAuth } from "../context/AuthContext";
import useDocumentTitle from "../hooks/useDocumentTitle";
import { inputClass, primaryButton } from "../ui";

export default function Register() {
  useDocumentTitle("Register");
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
    <AuthLayout
      title="Create your account"
      subtitle="It takes a few seconds."
      footer={
        <>
          Already registered?{" "}
          <Link
            to="/login"
            className="font-semibold text-indigo-600 hover:underline dark:text-indigo-400"
          >
            Log in
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

        <FormField
          label="Password (8 to 72 characters)"
          error={errors.password?.message}
        >
          <PasswordInput
            autoComplete="new-password"
            {...register("password", {
              required: "Password is required",
              minLength: { value: 8, message: "Use at least 8 characters" },
              maxLength: { value: 72, message: "Use at most 72 characters" },
            })}
          />
        </FormField>

        <FormField label="Confirm password" error={errors.confirm?.message}>
          <PasswordInput
            autoComplete="new-password"
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
          {isSubmitting ? "Creating account…" : "Create account"}
        </button>
      </form>
    </AuthLayout>
  );
}
