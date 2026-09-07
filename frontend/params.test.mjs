// Tests for params.js -- the parameter-detection/editing logic used by
// the Parameters panel. Pure logic, no DOM, so this runs directly under
// Node with no browser and no extra dependency (uses Node's built-in
// test runner, available since Node 18).
//
// Run with:  node --test frontend/params.test.mjs

import { test } from "node:test";
import assert from "node:assert/strict";

import { parseParams, formatParamLabel, formatParamLine } from "./params.js";


test("detects a simple numeric constant", () => {
    const params = parseParams("CARD_LENGTH = 88.0  # mm, long edge\n");
    assert.equal(params.length, 1);
    assert.equal(params[0].name, "CARD_LENGTH");
    assert.equal(params[0].type, "number");
    assert.equal(params[0].value, 88.0);
    assert.equal(params[0].isFloat, true);
    assert.equal(params[0].comment, "mm, long edge");
});

test("detects an integer without treating it as float", () => {
    const params = parseParams("NUM_CARDS = 108\n");
    assert.equal(params[0].isFloat, false);
    assert.equal(params[0].value, 108);
});

test("detects a boolean constant", () => {
    const params = parseParams("HEX_PATTERN = False  # honeycomb toggle\n");
    assert.equal(params[0].type, "bool");
    assert.equal(params[0].value, false);
});

test("detects a string constant and preserves quote style", () => {
    const params = parseParams('LID_TEXT = "Bobbie"  # engraved name\n');
    assert.equal(params[0].type, "string");
    assert.equal(params[0].value, "Bobbie");
    assert.equal(params[0].quote, '"');
});

test("single-quoted strings are detected too", () => {
    const params = parseParams("FONT = 'Arial'\n");
    assert.equal(params[0].value, "Arial");
    assert.equal(params[0].quote, "'");
});

test("ignores indented lines (inside functions/classes)", () => {
    const script = [
        "TOP_LEVEL = 1",
        "def f():",
        "    INDENTED = 2",
    ].join("\n");

    const params = parseParams(script);
    assert.equal(params.length, 1);
    assert.equal(params[0].name, "TOP_LEVEL");
});

test("ignores computed expressions -- only raw literals are editable", () => {
    const script = [
        "WALL = 2.4",
        "SLOT = WALL * 2 + 1",          // expression, not a literal
        "POSITIONS = [1, 2, 3]",         // list, not a literal
        "LABEL = f\"wall-{WALL}\"",      // f-string, not a plain literal
    ].join("\n");

    const params = parseParams(script);
    const names = params.map(p => p.name);

    assert.deepEqual(names, ["WALL"]);
});

test("ignores lowercase and mixed-case names (only ALL_CAPS constants)", () => {
    const script = [
        "CONSTANT = 1",
        "not_shouty = 2",
        "MixedCase = 3",
    ].join("\n");

    const params = parseParams(script);
    assert.deepEqual(params.map(p => p.name), ["CONSTANT"]);
});

test("records the correct line index for later rewriting", () => {
    const script = [
        "# a comment",
        "",
        "CARD_LENGTH = 88.0",
        "CARD_WIDTH = 63.0",
    ].join("\n");

    const params = parseParams(script);
    assert.equal(params.find(p => p.name === "CARD_LENGTH").lineIndex, 2);
    assert.equal(params.find(p => p.name === "CARD_WIDTH").lineIndex, 3);
});

test("a line with no trailing comment gets an empty comment string", () => {
    const params = parseParams("MOUTH_OVERLAP = 0.05\n");
    assert.equal(params[0].comment, "");
});

test("formatParamLabel converts SHOUTY_SNAKE_CASE to Title Case", () => {
    assert.equal(formatParamLabel("CARD_LENGTH"), "Card Length");
    assert.equal(formatParamLabel("NUM_DECKS"), "Num Decks");
    assert.equal(formatParamLabel("A"), "A");
});

test("formatParamLine reconstructs a bool line correctly", () => {
    const param = { name: "HEX_PATTERN", type: "bool", comment: "toggle" };
    assert.equal(
        formatParamLine(param, true),
        "HEX_PATTERN = True  # toggle"
    );
});

test("formatParamLine reconstructs a string line with original quote style", () => {
    const param = { name: "FONT", type: "string", quote: "'", comment: "" };
    assert.equal(formatParamLine(param, "Helvetica"), "FONT = 'Helvetica'");
});

test("formatParamLine reconstructs a number line", () => {
    const param = { name: "NUM_CARDS", type: "number", comment: "count" };
    assert.equal(
        formatParamLine(param, 120),
        "NUM_CARDS = 120  # count"
    );
});

test("round-trip: parse then reformat produces an equivalent line", () => {
    const original = "CARD_THICKNESS = 0.31  # mm per card";
    const [param] = parseParams(original);
    const rebuilt = formatParamLine(param, param.value);
    assert.equal(rebuilt, original);
});
