import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Modal } from "./Modal";

function renderModal(onClose = vi.fn()) {
  document.body.innerHTML = "";
  const trigger = document.createElement("button");
  trigger.textContent = "Open";
  document.body.appendChild(trigger);
  trigger.focus();

  render(
    <Modal open onClose={onClose} title="Test Modal">
      <input aria-label="First field" />
      <input aria-label="Second field" />
    </Modal>,
  );

  // DOM order inside the panel is: Close button, then the two children —
  // so the Close button is the actual first focusable element, not the
  // first child field.
  return {
    onClose,
    trigger,
    close: screen.getByLabelText("Close"),
    firstField: screen.getByLabelText("First field"),
    lastField: screen.getByLabelText("Second field"),
  };
}

describe("Modal", () => {
  it("moves focus inside the panel on open", () => {
    const { close } = renderModal();
    expect(close).toHaveFocus();
  });

  it("calls onClose on Escape", () => {
    const { onClose } = renderModal();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("wraps Tab from the last focusable element back to the first", () => {
    const { close, lastField } = renderModal();
    lastField.focus();
    fireEvent.keyDown(document, { key: "Tab" });
    expect(close).toHaveFocus();
  });

  it("wraps Shift+Tab from the first focusable element back to the last", () => {
    const { close, lastField } = renderModal();
    close.focus();
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(lastField).toHaveFocus();
  });

  it("returns focus to the trigger on close", () => {
    const onClose = vi.fn();
    document.body.innerHTML = "";
    const trigger = document.createElement("button");
    trigger.textContent = "Open";
    document.body.appendChild(trigger);
    trigger.focus();

    const { rerender } = render(
      <Modal open onClose={onClose} title="Test Modal">
        <input aria-label="First field" />
      </Modal>,
    );
    expect(trigger).not.toHaveFocus();

    rerender(
      <Modal open={false} onClose={onClose} title="Test Modal">
        <input aria-label="First field" />
      </Modal>,
    );
    expect(trigger).toHaveFocus();
  });
});
