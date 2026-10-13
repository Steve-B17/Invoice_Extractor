// Pulls the file name out of a Content-Disposition header such as:
//   attachment; filename="invoices-2026-10-12.csv"
export function filenameFromDisposition(header, fallback) {
  if (!header) return fallback;
  const encoded = /filename\*=UTF-8''([^;]+)/i.exec(header);
  if (encoded) {
    try {
      return decodeURIComponent(encoded[1].trim());
    } catch {
      return fallback;
    }
  }
  const plain = /filename="?([^";]+)"?/i.exec(header);
  const name = plain ? plain[1].trim() : "";
  // never let a server-supplied name contain a path
  return name && !/[\\/]/.test(name) ? name : fallback;
}

// Saves a Blob as a file in the browser
export function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
