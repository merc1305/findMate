import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the complete FindMate landing page", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>FindMate — Your agent finds your complementary founder<\/title>/i);
  assert.match(html, /Your agent can find/);
  assert.match(html, /your missing half\./);
  assert.match(html, /Own owner only/);
  assert.match(html, /A pool, not a people-search engine\./);
  assert.match(html, /No owner data is entered on this page\./);
  assert.match(html, /Created By Deerflow/);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton/i);
});

test("keeps the site privacy-first and removes starter artifacts", async () => {
  const [page, copyPrompt, layout, packageJson] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/CopyPrompt.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  assert.match(copyPrompt, /Do not mine old chats, email, contacts/);
  assert.match(copyPrompt, /navigator\.clipboard\.writeText/);
  assert.doesNotMatch(page + copyPrompt, /\bfetch\s*\(|XMLHttpRequest|localStorage/);
  assert.match(layout, /FindMate — Your agent finds your complementary founder/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);

  await assert.rejects(
    access(new URL("../app/_sites-preview", import.meta.url)),
  );
  await access(new URL("../public/og.png", import.meta.url));
});
