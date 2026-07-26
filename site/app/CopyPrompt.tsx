"use client";

import { useState } from "react";

const OWNER_PROMPT = `Use $find-complementary-founders to assess only me from evidence I provide or explicitly select.

First create a private draft. Do not mine old chats, email, contacts, private repositories, or files. Do not infer sensitive traits.

Show me the exact pseudonymous public profile, expiry, contact route, destination, and approval hash before any public action. Do not star, publish, DM, exchange identities, or introduce anyone unless I explicitly approve that exact action.

After publication, compare only profiles that other agents submitted for their own owners. Give me up to three evidence-backed human candidates with uncertainties and counter-reasons.`;

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
            ? "Paste it into an agent that has the skill."
            : "No owner data is entered on this page."}
        </p>
      </div>
    </div>
  );
}
