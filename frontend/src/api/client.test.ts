import { expect, it } from "vitest";
import { parseEvent } from "./client";

it("parses a token event", () => {
    const block = `event: token
data: {"text": "hello"}`;
    const result = parseEvent(block);
    expect(result).toEqual({ type: "token", text: "hello" });
});

it("parses a thinking event", () => {
    const block = `event: thinking
data: {"text": "let me think"}`;
    const result = parseEvent(block);
    expect(result).toEqual({ type: "thinking", text: "let me think" });
});

it("parses a sources event", () => {
    const block = `event: sources
data: [{"n": 1, "document": "a.pdf", "page": 1}]`;
    const result = parseEvent(block);
    expect(result).toEqual({
      type: "sources",
      sources: [{ n: 1, document: "a.pdf", page: 1 }],
    });
});

it("parses a done event", () => {
    const block = `event: done
data: {"message_id": 42}`;
    const result = parseEvent(block);
    expect(result).toEqual({ type: "done", messageId: 42 });
});

it("parses an error event", () => {
    const block = `event: error
data: {"detail": "boom", "code": "ollama_timeout"}`;
    const result = parseEvent(block);
    expect(result).toEqual({
      type: "error",
      detail: "boom",
      code: "ollama_timeout",
    });
});

it("parses a query event", () => {
    const block = `event: query
data: {"original": "what about it?", "query": "what is it?"}`;
    const result = parseEvent(block);
    expect(result).toEqual({
      type: "query",
      original: "what about it?",
      query: "what is it?",
    });
});

it("returns null for a block without an event name", () => {
    const block = `data: {"text": "hello"}`;
    expect(parseEvent(block)).toBeNull();
});

it("returns null for an empty block", () => {
    expect(parseEvent("")).toBeNull();
});
