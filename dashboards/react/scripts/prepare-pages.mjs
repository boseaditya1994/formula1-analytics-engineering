import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const indexPath = path.join(root, "dist", "client", "index.html");
// vinext shuts down a short-lived prerender process immediately after build.
// Let its final file handles settle before rewriting the exported entry point.
await new Promise((resolve) => setTimeout(resolve, 1000));
const html = await readFile(indexPath, "utf8");

// GitHub Pages serves this project below /formula1-analytics-engineering/. The
// static export's root-absolute assets would otherwise resolve at the profile root.
await writeFile(
  indexPath,
  html.replaceAll("/_next/", "./_next/"),
  "utf8",
);
