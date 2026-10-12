import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-slate-50">
      <p className="text-slate-700">That page does not exist.</p>
      <Link to="/" className="font-medium text-indigo-600 hover:underline">
        Go to your invoices
      </Link>
    </div>
  );
}
