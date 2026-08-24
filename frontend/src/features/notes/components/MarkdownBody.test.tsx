import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MarkdownBody } from "./MarkdownBody";

describe("MarkdownBody", () => {
  it("sends the correct zero-based line_index for a checkbox on the 7th line", () => {
    const body = [
      "# Heading", // line 1
      "", // line 2
      "Some intro text.", // line 3
      "", // line 4
      "## CORE OBJECTIVES", // line 5
      "- [ ] first item", // line 6
      "- [ ] second item", // line 7 (0-based index 6)
    ].join("\n");

    const onToggleCheckbox = vi.fn();
    render(<MarkdownBody body={body} onToggleCheckbox={onToggleCheckbox} />);

    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes).toHaveLength(2);

    checkboxes[1].click();
    expect(onToggleCheckbox).toHaveBeenCalledWith(6, true);
  });

  it("renders a blockquote with the pink warning class", () => {
    render(<MarkdownBody body="> a warning" onToggleCheckbox={vi.fn()} />);
    const quote = screen.getByText("a warning").closest("blockquote");
    expect(quote).toHaveClass("border-neon-pink");
  });
});
