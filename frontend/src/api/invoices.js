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

// Runs OCR and extraction again on a stored bill (replaces any edits)
export async function reprocessInvoice(id) {
  const { data } = await api.post(`/invoices/${id}/reprocess`);
  return data;
}

// Sends corrected fields. Only the fields in the body change, and the backend re-runs its checks.
export async function updateInvoice(id, payload) {
  const { data } = await api.patch(`/invoices/${id}`, payload);
  return data;
}

// Marks an invoice as checked by a person. force=true overrides remaining validation errors.
export async function verifyInvoice(id, force = false) {
  const { data } = await api.post(`/invoices/${id}/verify`, null, {
    params: force ? { force: true } : {},
  });
  return data;
}

// The original bill as a Blob. An <img src> tag cannot send the login header,
// so the file is fetched with the token and shown through a temporary local URL.
export async function fetchInvoiceFile(id) {
  const { data } = await api.get(`/invoices/${id}/file`, {
    responseType: "blob",
  });
  return data;
}
