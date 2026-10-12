// Checks a chosen file and, for very large photos, shrinks it before uploading.
//
// Why not shrink everything? The backend measures how big the text is and resizes it
// itself, so it only needs enough pixels to read the text. We only step in when a photo
// is big enough to be slow on mobile data or to risk the 10 MB upload limit.

export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024; // matches the backend's MAX_UPLOAD_MB
export const MAX_SIDE = 3600;
const RESIZE_ABOVE_BYTES = 6 * 1024 * 1024;
const JPEG_QUALITY = 0.9;

export const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "application/pdf"];
const EXTENSION_TYPES = {
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  png: "image/png",
  webp: "image/webp",
  pdf: "application/pdf",
};

export function detectType(file) {
  if (ALLOWED_TYPES.includes(file.type)) return file.type;
  const extension = file.name.split(".").pop()?.toLowerCase();
  return EXTENSION_TYPES[extension] ?? null;
}

export function typeProblem(file) {
  if (detectType(file)) return null;
  const extension = file.name.split(".").pop()?.toLowerCase();
  if (extension === "heic" || extension === "heif" || file.type === "image/heic") {
    return 'HEIC photos are not supported. Set your phone camera to "Most compatible" (JPEG), or use the Take photo button.';
  }
  return `"${file.name}" is not a supported file. Upload a JPG, PNG, WebP or PDF.`;
}

export function scaledSize(width, height, maxSide = MAX_SIDE) {
  const longest = Math.max(width, height);
  if (longest <= maxSide) return { width, height, scaled: false };
  const scale = maxSide / longest;
  return {
    width: Math.round(width * scale),
    height: Math.round(height * scale),
    scaled: true,
  };
}

export function shouldResize(file, width, height) {
  if (!file.type.startsWith("image/")) return false;
  return file.size > RESIZE_ABOVE_BYTES || Math.max(width, height) > MAX_SIDE;
}

export function jpegName(name) {
  const dot = name.lastIndexOf(".");
  return `${dot > 0 ? name.slice(0, dot) : name}.jpg`;
}

async function maybeResize(file) {
  let bitmap;
  try {
    // "from-image" applies the phone's rotation, so the pixels are already upright
    bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
  } catch {
    return file; // this browser cannot decode it: let the server decide
  }

  try {
    if (!shouldResize(file, bitmap.width, bitmap.height)) return file;

    const { width, height } = scaledSize(bitmap.width, bitmap.height);
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    canvas.getContext("2d").drawImage(bitmap, 0, 0, width, height);

    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", JPEG_QUALITY));
    if (!blob || blob.size >= file.size) return file; // never make a file bigger
    return new File([blob], jpegName(file.name), { type: "image/jpeg", lastModified: Date.now() });
  } finally {
    bitmap.close?.();
  }
}

// Returns the file to upload, or throws an Error with a message a person can read.
export async function prepareFile(file) {
  const problem = typeProblem(file);
  if (problem) throw new Error(problem);

  const prepared = file.type.startsWith("image/") ? await maybeResize(file) : file;
  if (prepared.size > MAX_UPLOAD_BYTES) {
    throw new Error(`"${file.name}" is larger than 10 MB. Try a smaller file.`);
  }
  return prepared;
}