import assert from "node:assert/strict";
import test from "node:test";
import {
  MAX_SIDE,
  detectType,
  jpegName,
  scaledSize,
  shouldResize,
  typeProblem,
} from "./prepareFile.js";

test("small photos keep their size", () => {
  assert.deepEqual(scaledSize(3000, 2000), {
    width: 3000,
    height: 2000,
    scaled: false,
  });
});

test("big photos shrink so the longest side fits, keeping the shape", () => {
  const result = scaledSize(8160, 3672);
  assert.equal(result.scaled, true);
  assert.equal(Math.max(result.width, result.height), MAX_SIDE);
  assert.ok(Math.abs(result.width / result.height - 8160 / 3672) < 0.01);
});

test("only large images are re-encoded", () => {
  assert.equal(
    shouldResize({ type: "image/jpeg", size: 2 * 1024 * 1024 }, 3000, 2000),
    false,
  );
  assert.equal(
    shouldResize({ type: "image/jpeg", size: 7 * 1024 * 1024 }, 3000, 2000),
    true,
  );
  assert.equal(
    shouldResize({ type: "image/jpeg", size: 1024 }, 8000, 3000),
    true,
  );
  assert.equal(
    shouldResize({ type: "application/pdf", size: 9 * 1024 * 1024 }, 0, 0),
    false,
  );
});

test("file types come from the type or the extension", () => {
  assert.equal(detectType({ name: "a.jpg", type: "image/jpeg" }), "image/jpeg");
  assert.equal(detectType({ name: "scan.PDF", type: "" }), "application/pdf");
  assert.equal(detectType({ name: "photo.heic", type: "image/heic" }), null);
  assert.equal(detectType({ name: "notes.txt", type: "text/plain" }), null);
});

test("unsupported files get a readable explanation", () => {
  assert.match(typeProblem({ name: "IMG_1.HEIC", type: "" }), /HEIC/);
  assert.match(
    typeProblem({ name: "notes.txt", type: "text/plain" }),
    /not a supported file/,
  );
  assert.equal(typeProblem({ name: "bill.png", type: "image/png" }), null);
});

test("resized photos are named .jpg", () => {
  assert.equal(jpegName("bill.png"), "bill.jpg");
  assert.equal(jpegName("my.bill.final.webp"), "my.bill.final.jpg");
  assert.equal(jpegName("noextension"), "noextension.jpg");
});
