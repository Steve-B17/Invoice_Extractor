import { api } from "./client";

export async function listInvoices() {
  const { data } = await api.get("/invoices", { params: { limit: 100 } });
  return data;
}
