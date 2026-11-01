// ------------------------------------------------------------
// PARAMETER PARSING (pure logic, no DOM)
//
// Detects top-level constant assignments in a script
// (NAME = literal_value  # optional comment) so they can be exposed
// as form controls. Split out from app.js specifically so this logic
// is testable with a plain Node test runner -- no browser needed.
// ------------------------------------------------------------

export const PARAM_LINE_PATTERN =
    /^([A-Z][A-Z0-9_]*)\s*=\s*(.+?)\s*(#.*)?$/;


export function parseParams(scriptText) {

    const lines =
        scriptText.split("\n");

    const params = [];

    for (let i = 0; i < lines.length; i++) {

        const line = lines[i];

        // Only bare (non-indented) lines count as top-level constants --
        // this naturally skips anything inside a function/class body.
        if (/^\s/.test(line) || !line.trim()) {
            continue;
        }

        const match =
            line.match(PARAM_LINE_PATTERN);

        if (!match) {
            continue;
        }

        const [, name, rawValue, rawComment] = match;

        let type = null;
        let value = null;

        if (/^(True|False)$/.test(rawValue)) {

            type = "bool";
            value = rawValue === "True";

        } else if (/^-?\d+(\.\d+)?$/.test(rawValue)) {

            type = "number";
            value = Number(rawValue);

        } else if (/^(['"]).*\1$/.test(rawValue)) {

            type = "string";
            value = rawValue.slice(1, -1);
        }

        // Anything else (expressions, list comprehensions, function
        // calls referencing other constants) is left alone -- it's
        // derived, not a raw literal a person would hand-tune.
        if (type === null) {
            continue;
        }

        params.push({
            lineIndex: i,
            name: name,
            type: type,
            value: value,
            isFloat: type === "number" && rawValue.includes("."),
            quote: type === "string" ? rawValue[0] : null,
            comment:
                rawComment
                    ? rawComment.replace(/^#\s*/, "")
                    : ""
        });
    }

    return params;
}


export function formatParamLabel(name) {

    return name
        .toLowerCase()
        .split("_")
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
}


export function formatParamLine(param, newValue) {

    let formattedValue;

    if (param.type === "bool") {
        formattedValue = newValue ? "True" : "False";
    } else if (param.type === "string") {
        formattedValue = param.quote + newValue + param.quote;
    } else {
        formattedValue = String(newValue);
    }

    const commentSuffix =
        param.comment ? "  # " + param.comment : "";

    return `${param.name} = ${formattedValue}${commentSuffix}`;
}


// A string constant gets a "Browse..." button (native file picker) when its
// name ends in IMAGE / PATH / FILE, or its comment carries a [browse] tag.
export const FILE_PARAM_NAME = /(IMAGE|PATH|FILE)$/;


export function isFilePathParam(param) {

    return param.type === "string" && (
        FILE_PARAM_NAME.test(param.name) ||
        /\[browse\]/i.test(param.comment)
    );
}


// Hint text shown under the label: the [browse] tag is a marker for the
// UI, not something to display. (The stored comment keeps it, so saving a
// changed value never drops the tag from the script.)
export function displayComment(comment) {

    return comment.replace(/\s*\[browse\]\s*/i, " ").trim();
}
