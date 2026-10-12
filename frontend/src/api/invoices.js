import { api } from "./client";

export async function listInvoices() {
  const { data } = await api.get("/invoices", { params: { limit: 100 } });
  return data;
}

export async function getInvoice(id) {
  const { data } = await api.get(`/invoices/${id}`);
  return data;
}

// Sends one file. onProgress receives a number from 0 to 100.
export async function uploadInvoice(file, onProgress) {
  const body = new FormData();
  body.append("file", file);
  const { data } = await api.post("/invoices", body, {
    onUploadProgress: (event) => {
      if (event.total)
        onProgress?.(Math.round((event.loaded * 100) / event.total));
    },
  });
  return data;
}

// Runs OCR and extraction again on a stored bill
export async function reprocessInvoice(id) {
  const { data } = await api.post(`/invoices/${id}/reprocess`);
  return data;
}
