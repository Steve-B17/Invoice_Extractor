import { Link } from "react-router-dom";
import Logo from "../components/Logo";
import useDocumentTitle from "../hooks/useDocumentTitle";
import { primaryButton } from "../ui";

export default function NotFound() {
  useDocumentTitle("Page not found");
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-5 bg-slate-50 px-4 text-center dark:bg-slate-900 dark:text-slate-200">
      <Logo />
      <p className="text-6xl font-bold tracking-tight text-slate-300 dark:text-slate-600">404</p>
      <p className="text-slate-600 dark:text-slate-300">That page does not exist.</p>
      <Link to="/" className={primaryButton}>
        Go to your invoices
      </Link>
    </div>
  );
}
