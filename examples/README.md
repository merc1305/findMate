# Synthetic FindMate demo

Run the complete assessment-and-matching path without owner data, credentials,
network access, or public actions:

```bash
python3 examples/run_synthetic_demo.py
```

The script creates two temporary public profiles:

- `synthetic-builder` demonstrates `0→1`, product, and engineering;
- `synthetic-operator` demonstrates `1→10`, go-to-market, and operations.

Each seeks the other's demonstrated capabilities. The normal deterministic
matcher validates both profiles and prints reciprocal gap coverage, alignment,
evidence quality, reasons, and a shortlist score.

All evidence is explicitly synthetic. Public profile files live only inside a
temporary directory and are deleted when the run finishes. The demo never
creates a private assessment file, calls Moltbook, changes GitHub, or emits
telemetry.

To inspect the human-readable private result without using owner data, open the
[fully synthetic Founder Complement Canvas](../skills/find-complementary-founders/references/example-founder-complement-canvas.md).
It is an exact output of the same private renderer and contains no contact
route, proof URL, consent field, or raw note.
