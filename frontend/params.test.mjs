// Tests for params.js -- the parameter-detection/editing logic used by
// the Parameters panel. Pure logic, no DOM, so this runs directly under
// Node with no browser and no extra dependency (uses Node's built-in
// test runner, available since Node 18).
//
// Run with:  node --test frontend/params.test.mjs

import { test } from "node:test";
import assert from "node:assert/strict";

import {
    parseParams, formatParamLabel, formatParamLine,
    isFilePathParam, displayComment, parseChoices, parseWhen, isParamVisible
} from "./params.js";


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


test("isFilePathParam: IMAGE/PATH/FILE names and [browse] tag, strings only", () => {
    const [img] = parseParams('LID_IMAGE = ""  # pick one');
    assert.equal(isFilePathParam(img), true);

    const [tagged] = parseParams('LOGO = ""  # [browse] logo');
    assert.equal(isFilePathParam(tagged), true);

    const [plain] = parseParams('FONT = "Arial"  # typeface');
    assert.equal(isFilePathParam(plain), false);

    const [num] = parseParams('IMAGE_SCALE = 100  # percent');
    assert.equal(isFilePathParam(num), false);

    const [flag] = parseParams('USE_IMAGE = True  # on/off');
    assert.equal(isFilePathParam(flag), false);
});

test("displayComment hides the [browse] tag but formatParamLine keeps it", () => {
    const line = 'LID_IMAGE = ""  # [browse] image for the lid';
    const [param] = parseParams(line);
    assert.equal(displayComment(param.comment), "image for the lid");
    assert.equal(formatParamLine(param, "/tmp/a.png"),
        'LID_IMAGE = "/tmp/a.png"  # [browse] image for the lid');
});

test("parses the card-box LID_IMAGE line with a long comment", () => {
    const [param] = parseParams(
        'LID_IMAGE      = ""        # [browse] image engraved on the lid instead of the name ("" = use the name)');
    assert.equal(param.name, "LID_IMAGE");
    assert.equal(param.value, "");
    assert.equal(isFilePathParam(param), true);
});


test("parseChoices reads [choice: a|b|c] on string params only", () => {
    const [art] = parseParams('LID_ART = "text"  # [choice: blank|text|image] what the lid shows');
    assert.deepEqual(parseChoices(art), ["blank", "text", "image"]);
    assert.equal(displayComment(art.comment), "what the lid shows");

    const [num] = parseParams("N = 3  # [choice: a|b] nope");
    assert.equal(parseChoices(num), null);

    const [none] = parseParams('FONT = "Arial"  # typeface');
    assert.equal(parseChoices(none), null);

    const [one] = parseParams('X = "a"  # [choice: a] only one option');
    assert.equal(parseChoices(one), null);
});

test("choice tag survives a value change (round trip)", () => {
    const line = 'LID_ART = "text"  # [choice: blank|text|image] what the lid shows';
    const [param] = parseParams(line);
    assert.equal(formatParamLine(param, "image"),
        'LID_ART = "image"  # [choice: blank|text|image] what the lid shows');
});

test("[when NAME=value] shows a row only while the controller matches", () => {
    const params = parseParams([
        'LID_ART = "image"  # [choice: blank|text|image] mode',
        'LID_TEXT = "Bobbie"  # [when LID_ART=text] name',
        'LID_IMAGE = ""  # [browse] [when LID_ART=image] picture',
        'HEX = True  # honeycomb',
        'HEX_SIZE = 6  # [when HEX=true] size',
    ].join("\n"));

    const visible = params.filter(p => isParamVisible(p, params)).map(p => p.name);
    assert.deepEqual(visible, ["LID_ART", "LID_IMAGE", "HEX", "HEX_SIZE"]);

    assert.deepEqual(parseWhen(params[1]), { name: "LID_ART", value: "text" });
    assert.equal(displayComment(params[2].comment), "picture");
});

test("[when ...] with an unknown controller never hides the row", () => {
    const params = parseParams('A = 1  # [when MISSING=x] still shown');
    assert.equal(isParamVisible(params[0], params), true);
});
