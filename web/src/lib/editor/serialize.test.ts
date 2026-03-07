import { describe, expect, it } from "vitest";

import { deserializeEditorDoc, serializeEditorDoc } from "./serialize";

describe("serializeEditorDoc", () => {
  it("round-trips editor JSON", () => {
    const doc = {
      type: "doc",
      content: [
        {
          type: "paragraph",
          content: [{ type: "text", text: "NeuroNote captures ideas." }],
        },
      ],
    };

    const serialized = serializeEditorDoc(doc);
    const deserialized = deserializeEditorDoc(serialized);

    expect(deserialized).toEqual(doc);
  });

  it("returns an empty document for invalid JSON payloads", () => {
    const parsed = deserializeEditorDoc("not-json");
    expect(parsed).toEqual({ type: "doc", content: [] });
  });
});
