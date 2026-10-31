// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import type { Source } from "../api/types";
import SourceDrawer from "./SourceDrawer";

it("offers the full chunk even when it matches the preview", () => {
  const text = "A short chunk that fits entirely in the preview.";
  const source: Source = {
    n: 1,
    document_id: "document-1",
    document: "notes.txt",
    page: null,
    distance: 0.1,
    snippet: text,
    text,
  };

  render(
    <SourceDrawer
      sources={[source]}
      active={null}
      onSelect={() => {}}
      onClose={() => {}}
    />,
  );

  expect(screen.getByText("View full chunk")).toBeTruthy();
});
