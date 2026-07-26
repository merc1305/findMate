"use client";

import { useState } from "react";

const OWNER_PROMPT = `Read the public FindMate skill before acting:
https://github.com/merc1305/findMate/blob/main/skills/find-complementary-founders/SKILL.md

Use it to assess only me. For this first pass, ask me for two or three outcomes and public artifacts that I personally produced. Use only evidence I provide in this conversation or explicitly select.

Create only a private draft: demonstrated 0→1, 1→10, and 10→100 stages; demonstrated functions; evidence and confidence; capability gaps; missing evidence; and a privacy-risk check. Keep unknowns unknown.

Do not install software, mine old chats, read email, contacts, private repositories, or files, infer sensitive traits, create a public profile, star, publish, DM, exchange identities, or introduce anyone.

Stop after showing me the private draft and the optional next steps. If you cannot read the public skill URL, say so and stop.`;

export function CopyPrompt() {
  const [copied, setCopied] = useState(false);

  async function copyPrompt() {
    try {
      await navigator.clipboard.writeText(OWNER_PROMPT);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2400);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="prompt-console">
      <div className="console-bar">
        <span>owner_request.txt</span>
        <span className="local-only">PRIVATE DRAFT FIRST</span>
      </div>
      <pre>{OWNER_PROMPT}</pre>
      <div className="console-actions">
        <button type="button" onClick={copyPrompt} className="copy-button">
          <span aria-hidden="true">{copied ? "✓" : "↗"}</span>
          {copied ? "Copied" : "Copy safe prompt"}
        </button>
        <p aria-live="polite">
          {copied
            ? "Paste it into any agent that can read public GitHub links."
            : "No owner data is entered on this page."}
        </p>
      </div>
    </div>
  );
}
