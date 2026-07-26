import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

async function render(pathname = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request(`http://localhost${pathname}`, {
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

test("serves crawler discovery metadata", async () => {
  const [robotsResponse, sitemapResponse] = await Promise.all([
    render("/robots.txt"),
    render("/sitemap.xml"),
  ]);

  assert.equal(robotsResponse.status, 200);
  assert.match(robotsResponse.headers.get("content-type") ?? "", /^text\/plain\b/i);
  const robots = await robotsResponse.text();
  assert.match(robots, /User-Agent: \*/);
  assert.match(robots, /Allow: \//);
  assert.match(robots, /Sitemap: https:\/\/findmate-owner-network\.xvwbgtt855\.chatgpt\.site\/sitemap\.xml/);

  assert.equal(sitemapResponse.status, 200);
  assert.match(sitemapResponse.headers.get("content-type") ?? "", /^application\/xml\b/i);
  const sitemap = await sitemapResponse.text();
  assert.match(sitemap, /<loc>https:\/\/findmate-owner-network\.xvwbgtt855\.chatgpt\.site<\/loc>/);
});

test("server-renders the complete FindMate landing page", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>FindMate — Your agent finds your complementary founder<\/title>/i);
  assert.match(html, /Your agent can find/);
  assert.match(html, /your missing half\./);
  assert.match(html, /Own owner only/);
  assert.match(html, /No pre-install\. Zero silent actions\./);
  assert.match(html, /A pool, not a people-search engine\./);
  assert.match(html, /no separate profile repository/i);
  assert.match(html, /No owner data is entered on this page\./);
  assert.match(html, /rel="canonical" href="https:\/\/findmate-owner-network\.xvwbgtt855\.chatgpt\.site\/?"/);
  assert.match(html, /href="\/llms\.txt">Agent index/);
  assert.match(html, /Created By Deerflow/);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton/i);
});

test("keeps the site privacy-first and exposes bounded discovery files", async () => {
  const [page, copyPrompt, layout, robots, sitemap, llms, packageJson] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/CopyPrompt.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/robots.ts", import.meta.url), "utf8"),
    readFile(new URL("../app/sitemap.ts", import.meta.url), "utf8"),
    readFile(new URL("../public/llms.txt", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  assert.match(
    copyPrompt,
    /Do not install software, mine old chats, read email, contacts/,
  );
  assert.match(copyPrompt, /github\.com\/merc1305\/findMate\/blob\/main\/skills/);
  assert.match(copyPrompt, /Create only a private draft/);
  assert.match(copyPrompt, /Do not install software/);
  assert.doesNotMatch(copyPrompt, /agent that has the skill/);
  assert.match(copyPrompt, /navigator\.clipboard\.writeText/);
  assert.doesNotMatch(page + copyPrompt, /\bfetch\s*\(|XMLHttpRequest|localStorage/);
  assert.match(layout, /FindMate — Your agent finds your complementary founder/);
  assert.match(layout, /canonical: "\/"/);
  assert.match(robots, /sitemap\.xml/);
  assert.match(sitemap, /changeFrequency: "weekly"/);
  assert.match(llms, /^# FindMate/m);
  assert.match(llms, /assess only its own owner/);
  assert.match(llms, /Never infer a profile for another agent's owner/);
  assert.match(llms, /Canonical Agent Skill/);
  assert.doesNotMatch(llms, /auto(?:matically)? star|silent(?:ly)? star/i);
  assert.doesNotMatch(packageJson, /react-loading-skeleton/);

  await assert.rejects(
    access(new URL("../app/_sites-preview", import.meta.url)),
  );
  await access(new URL("../public/og.png", import.meta.url));
});
