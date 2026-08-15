import { parseEvidence } from "@api/_evidence";
import { describe, expect, it } from "vitest";

describe("parseEvidence with nothing to show", () => {
  it("returns nothing for an absent or blank field", () => {
    expect(parseEvidence(undefined)).toEqual([]);
    expect(parseEvidence("")).toEqual([]);
    expect(parseEvidence("   ")).toEqual([]);
  });

  it("returns nothing for an empty JSON array", () => {
    expect(parseEvidence("[]")).toEqual([]);
  });

  it("drops an entry whose every value is empty", () => {
    expect(parseEvidence('[{"quote":"","page":null}]')).toEqual([]);
  });
});

describe("parseEvidence with plain text", () => {
  it("wraps text that is not JSON at all", () => {
    expect(parseEvidence("just a quote")).toEqual([
      { index: 0, fields: [{ key: "text", value: "just a quote" }] },
    ]);
  });

  it("trims the text it wraps", () => {
    expect(parseEvidence("  spaced  ")[0].fields[0].value).toBe("spaced");
  });

  it("reads a bare number as JSON, not as text", () => {
    expect(parseEvidence("123")).toEqual([
      { index: 0, fields: [{ key: "text", value: "123" }] },
    ]);
  });
});

describe("parseEvidence with structured data", () => {
  it("turns each object in an array into an item", () => {
    expect(parseEvidence('[{"quote":"a"},{"quote":"b"}]')).toEqual([
      { index: 0, fields: [{ key: "quote", value: "a" }] },
      { index: 1, fields: [{ key: "quote", value: "b" }] },
    ]);
  });

  it("accepts a lone object as a single item", () => {
    expect(parseEvidence('{"quote":"a","page":3}')).toEqual([
      {
        index: 0,
        fields: [
          { key: "quote", value: "a" },
          { key: "page", value: "3" },
        ],
      },
    ]);
  });

  it("renders numbers and booleans as text", () => {
    expect(parseEvidence('[{"page":3,"verified":false}]')[0].fields).toEqual([
      { key: "page", value: "3" },
      { key: "verified", value: "false" },
    ]);
  });

  it("joins a list of values", () => {
    expect(parseEvidence('[{"quotes":["one","two"]}]')[0].fields).toEqual([
      { key: "quotes", value: "one; two" },
    ]);
  });

  it("drops the empty entries of a list", () => {
    expect(parseEvidence('[{"quotes":["one","","two"]}]')[0].fields).toEqual([
      { key: "quotes", value: "one; two" },
    ]);
  });

  it("falls back to JSON for a nested object", () => {
    expect(parseEvidence('[{"meta":{"page":3}}]')[0].fields).toEqual([
      { key: "meta", value: '{"page":3}' },
    ]);
  });

  it("keeps the populated keys of a partly empty entry", () => {
    expect(parseEvidence('[{"quote":"a","page":null}]')[0].fields).toEqual([
      { key: "quote", value: "a" },
    ]);
  });

  it("numbers the items it keeps by their position in the input", () => {
    const items = parseEvidence('[{"quote":"a"},{"quote":""},{"quote":"c"}]');
    expect(items.map((item) => item.index)).toEqual([0, 2]);
  });
});
