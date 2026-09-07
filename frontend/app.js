import * as THREE from
    'https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js';

import { OrbitControls } from
    'https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/controls/OrbitControls.js';

import { STLLoader } from
    'https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/loaders/STLLoader.js';


// ------------------------------------------------------------
// DEFAULT BUILD123D SCRIPT
// ------------------------------------------------------------

const defaultScript = `from build123d import *

box = Box(50, 40, 20)

export_stl(box, "model.stl")
`;

document.getElementById("script").value =
    defaultScript;


// ------------------------------------------------------------
// THREE.JS SCENE
// ------------------------------------------------------------

const scene = new THREE.Scene();

scene.background =
    new THREE.Color(0x0e0f13);


// ------------------------------------------------------------
// CAMERA
// ------------------------------------------------------------

const camera =
    new THREE.PerspectiveCamera(
        45,
        1,
        0.1,
        10000
    );

camera.position.set(
    80,
    80,
    80
);


// ------------------------------------------------------------
// RENDERER
// ------------------------------------------------------------

const renderer =
    new THREE.WebGLRenderer({
        antialias: true
    });

renderer.setPixelRatio(
    window.devicePixelRatio
);

document
    .getElementById("viewer")
    .appendChild(renderer.domElement);


// ------------------------------------------------------------
// ORBIT CONTROLS
// ------------------------------------------------------------

const controls =
    new OrbitControls(
        camera,
        renderer.domElement
    );

controls.enableDamping = true;


// ------------------------------------------------------------
// LIGHTING
// ------------------------------------------------------------

const ambientLight =
    new THREE.AmbientLight(
        0xffffff,
        1.5
    );

scene.add(
    ambientLight
);


const directionalLight =
    new THREE.DirectionalLight(
        0xffffff,
        2
    );

directionalLight.position.set(
    100,
    100,
    100
);

scene.add(
    directionalLight
);


// ------------------------------------------------------------
// GRID
// ------------------------------------------------------------

const grid =
    new THREE.GridHelper(
        200,
        20
    );

scene.add(grid);


// ------------------------------------------------------------
// CURRENT MODEL
// ------------------------------------------------------------

let currentModel = null;


// ------------------------------------------------------------
// VIEWPORT RESIZING
// ------------------------------------------------------------

function resizeViewer() {

    const container =
        document.getElementById("viewer");

    const width =
        container.clientWidth;

    const height =
        container.clientHeight;

    camera.aspect =
        width / height;

    camera.updateProjectionMatrix();

    renderer.setSize(
        width,
        height
    );
}


window.addEventListener(
    "resize",
    resizeViewer
);

resizeViewer();


// ------------------------------------------------------------
// RENDER LOOP
// ------------------------------------------------------------

function animate() {

    requestAnimationFrame(
        animate
    );

    controls.update();

    renderer.render(
        scene,
        camera
    );
}

animate();


// ------------------------------------------------------------
// LOAD STL
// ------------------------------------------------------------

async function loadModel(name) {

    const response =
        await fetch(
            "/model/" + encodeURIComponent(name)
        );

    if (!response.ok) {

        throw new Error(
            "Could not load generated model."
        );
    }


    const arrayBuffer =
        await response.arrayBuffer();


    const loader =
        new STLLoader();


    const geometry =
        loader.parse(
            arrayBuffer
        );


    // STL / build123d use Z-up (same convention as your slicer's bed
    // view). Three.js defaults to Y-up. Without this rotation the model
    // renders tipped 90° on its side instead of resting the way it would
    // sit on a print bed.
    geometry.rotateX(-Math.PI / 2);


    geometry.computeVertexNormals();


    const material =
        new THREE.MeshStandardMaterial({
            color: 0xfe6e31,
            metalness: 0.1,
            roughness: 0.7
        });


    const mesh =
        new THREE.Mesh(
            geometry,
            material
        );


    // Remove previous model

    if (currentModel) {

        scene.remove(
            currentModel
        );

        currentModel.geometry.dispose();

        currentModel.material.dispose();
    }


    currentModel =
        mesh;

    scene.add(
        currentModel
    );


    // --------------------------------------------------------
    // CENTER MODEL (horizontally) AND REST IT ON THE GRID
    // --------------------------------------------------------

    geometry.computeBoundingBox();

    const box =
        geometry.boundingBox;

    const center =
        new THREE.Vector3();

    box.getCenter(
        center
    );

    // Center over the origin on X/Z, but keep the model's lowest point
    // at y=0 -- resting on the grid like it would on a print bed, rather
    // than floating with its vertical center at the origin.
    mesh.position.set(
        -center.x,
        -box.min.y,
        -center.z
    );


    // --------------------------------------------------------
    // FIT CAMERA
    // --------------------------------------------------------

    const size =
        new THREE.Vector3();

    box.getSize(
        size
    );

    const maxDimension =
        Math.max(
            size.x,
            size.y,
            size.z
        );


    camera.position.set(
        maxDimension * 1.5,
        maxDimension * 1.5,
        maxDimension * 1.5
    );


    controls.target.set(
        0,
        size.y / 2,
        0
    );

    controls.update();
}


// ------------------------------------------------------------
// FILE LIST (multiple STL outputs from one build)
// ------------------------------------------------------------

function renderFileList(names, panel) {

    for (const name of names) {

        const row =
            document.createElement("div");

        row.className = "file-row";

        row.dataset.name = name;


        const nameButton =
            document.createElement("button");

        nameButton.className = "file-name";

        nameButton.textContent = name;

        nameButton.addEventListener(
            "click",
            () => selectFile(name, panel)
        );


        const downloadLink =
            document.createElement("a");

        downloadLink.className = "file-download";

        downloadLink.href =
            "/download/" + encodeURIComponent(name);

        downloadLink.textContent = "Download";

        downloadLink.download =
            name.split("/").pop();


        const slicerButton =
            document.createElement("button");

        slicerButton.className = "file-slicer";

        slicerButton.textContent = "Open in OrcaSlicer";

        slicerButton.addEventListener(
            "click",
            () => openInSlicer(name, slicerButton)
        );


        const actions =
            document.createElement("div");

        actions.className = "file-actions";

        actions.appendChild(slicerButton);
        actions.appendChild(downloadLink);


        row.appendChild(nameButton);
        row.appendChild(actions);
        panel.appendChild(row);
    }
}


async function openInSlicer(name, button) {

    const originalText =
        button.textContent;

    button.textContent = "Opening...";

    button.disabled = true;

    try {

        const response =
            await fetch(
                "/open-in-slicer/" + encodeURIComponent(name),
                { method: "POST" }
            );

        if (!response.ok) {

            const body =
                await response.json().catch(
                    () => ({})
                );

            throw new Error(
                body.detail || "Failed to open in OrcaSlicer."
            );
        }

        button.textContent = "Opened!";

    }
    catch (error) {

        button.textContent = "Failed";

        console.error(error.message);
    }
    finally {

        setTimeout(
            () => {
                button.textContent = originalText;
                button.disabled = false;
            },
            2000
        );
    }
}


async function selectFile(name, panel) {

    await loadModel(name);

    for (const row of panel.children) {

        row.classList.toggle(
            "active",
            row.dataset.name === name
        );
    }
}


// ------------------------------------------------------------
// STATUS BAR
// ------------------------------------------------------------

function setStatus(state, label) {

    const dot =
        document.getElementById("status-dot");

    const text =
        document.getElementById("status-text");

    dot.className =
        "status-dot" + (state ? " " + state : "");

    text.textContent = label;
}


// ------------------------------------------------------------
// PARAMETER EDITING
//
// Detects top-level constant assignments in the script
// (NAME = literal_value  # optional comment) and exposes them as
// form controls. Editing a control rewrites that exact line in the
// textarea -- the textarea stays the single source of truth, this
// is just a friendly editor bound to specific lines in it.
// ------------------------------------------------------------

const PARAM_LINE_PATTERN =
    /^([A-Z][A-Z0-9_]*)\s*=\s*(.+?)\s*(#.*)?$/;


function parseParams(scriptText) {

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


function formatParamLabel(name) {

    return name
        .toLowerCase()
        .split("_")
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(" ");
}


function writeParamValue(param, newValue) {

    const scriptBox =
        document.getElementById("script");

    const lines =
        scriptBox.value.split("\n");

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

    lines[param.lineIndex] =
        `${param.name} = ${formattedValue}${commentSuffix}`;

    scriptBox.value = lines.join("\n");
}


function renderParamsPanel() {

    const scriptBox =
        document.getElementById("script");

    const panel =
        document.getElementById("params");

    const params =
        parseParams(scriptBox.value);

    panel.innerHTML = "";

    for (const param of params) {

        const row =
            document.createElement("div");

        row.className = "param-row";


        const info =
            document.createElement("div");

        info.className = "param-info";


        const label =
            document.createElement("div");

        label.className = "param-label";

        label.textContent =
            formatParamLabel(param.name);

        info.appendChild(label);


        if (param.comment) {

            const hint =
                document.createElement("div");

            hint.className = "param-hint";

            hint.textContent = param.comment;

            hint.title = param.comment;

            info.appendChild(hint);
        }


        const controlWrap =
            document.createElement("div");

        controlWrap.className = "param-control";

        const input =
            document.createElement("input");

        if (param.type === "bool") {

            input.type = "checkbox";

            input.checked = param.value;

            input.addEventListener(
                "change",
                () => writeParamValue(param, input.checked)
            );

        } else if (param.type === "number") {

            input.type = "number";

            input.value = param.value;

            input.step = param.isFloat ? "any" : "1";

            input.addEventListener(
                "change",
                () => writeParamValue(param, Number(input.value))
            );

        } else {

            input.type = "text";

            input.value = param.value;

            input.addEventListener(
                "change",
                () => writeParamValue(param, input.value)
            );
        }

        controlWrap.appendChild(input);

        row.appendChild(info);
        row.appendChild(controlWrap);
        panel.appendChild(row);
    }
}


// Re-scan whenever the script changes: on load, after opening a file,
// and (debounced) as the person types directly in the editor.

let paramRefreshTimer = null;

function scheduleParamRefresh() {

    clearTimeout(paramRefreshTimer);

    paramRefreshTimer =
        setTimeout(renderParamsPanel, 400);
}

document
    .getElementById("script")
    .addEventListener(
        "input",
        scheduleParamRefresh
    );

// Now that parseParams/renderParamsPanel exist, render the default script's
// params. (This has to happen after their declarations below this point in
// module-load order, not up near where defaultScript is set.)
renderParamsPanel();


// ------------------------------------------------------------
// BUILD
// ------------------------------------------------------------

async function build() {

    const buildButton =
        document.getElementById("build-button");

    const script =
        document.getElementById(
            "script"
        ).value;

    const output =
        document.getElementById(
            "output"
        );


    buildButton.disabled = true;

    output.textContent =
        "Building...";

    setStatus("building", "Building…");


    try {

        const response =
            await fetch(
                "/build",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        script: script
                    })
                }
            );


        const result =
            await response.json();


        output.textContent =
            result.output;


        const filesPanel =
            document.getElementById("files");

        filesPanel.innerHTML = "";


        if (result.success && result.files.length > 0) {

            renderFileList(
                result.files,
                filesPanel
            );

            // Auto-load the first file so the viewer isn't left empty
            await selectFile(
                result.files[0],
                filesPanel
            );

            setStatus(
                "success",
                result.files.length === 1
                    ? "Built 1 file"
                    : `Built ${result.files.length} files`
            );

        } else if (!result.files.length) {

            output.textContent +=
                "\n\n(Script ran but produced no .stl files.)";

            setStatus("error", "No .stl files produced");

        } else {

            setStatus("error", "Build failed");
        }

    }
    catch (error) {

        output.textContent =
            "Error: " +
            error.message;

        setStatus("error", "Build failed");
    }
    finally {

        buildButton.disabled = false;
    }
}


// ------------------------------------------------------------
// BUILD BUTTON
// ------------------------------------------------------------

document
    .getElementById("build-button")
    .addEventListener(
        "click",
        build
    );

// ------------------------------------------------------------
// FILE STATE (open/save)
// ------------------------------------------------------------

// Set once pywebview's bridge is ready (see bottom of this section).
// Until then, or if this page is ever opened in a plain browser instead
// of the desktop shell, we fall back to the old <input type="file">
// picker and a manual "Save As" only (no real path -> no true "Save").
let hasNativeApi = false;

let currentFilePath = null;
let currentFileName = null;


function updateFileLabel() {

    const label =
        document.getElementById("current-file");

    label.textContent =
        currentFileName || "";

    document.getElementById("save-button").disabled =
        !currentFilePath;
}


function setCurrentFile(path, name) {

    currentFilePath = path;
    currentFileName = name;

    updateFileLabel();
}


async function loadScriptText(text, name, path) {

    document.getElementById("script").value = text;

    renderParamsPanel();

    setCurrentFile(path || null, name || null);

    document.getElementById("output").textContent =
        name ? `Opened: ${name}` : "Ready.";
}


// ------------------------------------------------------------
// OPEN
// ------------------------------------------------------------

const openButton =
    document.getElementById("open-button");

const fileInput =
    document.getElementById("file-input");


async function openNative() {

    const result =
        await window.pywebview.api.open_file();

    if (!result) {
        return;
    }

    if (result.error) {
        document.getElementById("output").textContent =
            "Error opening file: " + result.error;
        return;
    }

    await loadScriptText(
        result.content,
        result.name,
        result.path
    );
}


openButton.addEventListener(
    "click",
    () => {

        if (hasNativeApi) {
            openNative();
        } else {
            fileInput.click();
        }
    }
);


// Browser-only fallback (no real path available from a picked file, so
// this can't set currentFilePath -- "Save" stays disabled until a
// "Save As" happens through the native API).
fileInput.addEventListener(
    "change",
    async (event) => {

        const file =
            event.target.files[0];

        if (!file) {
            return;
        }

        const contents =
            await file.text();

        await loadScriptText(contents, file.name, null);

        // Allow opening the same file again later
        fileInput.value = "";
    }
);


// ------------------------------------------------------------
// SAVE / SAVE AS
// ------------------------------------------------------------

const saveButton =
    document.getElementById("save-button");

const saveAsButton =
    document.getElementById("save-as-button");


saveButton.addEventListener(
    "click",
    async () => {

        if (!hasNativeApi || !currentFilePath) {
            return;
        }

        const script =
            document.getElementById("script").value;

        const result =
            await window.pywebview.api.save_file(
                script,
                currentFilePath
            );

        if (result && result.error) {
            document.getElementById("output").textContent =
                "Error saving file: " + result.error;
            return;
        }

        document.getElementById("output").textContent =
            `Saved: ${currentFileName}`;
    }
);


saveAsButton.addEventListener(
    "click",
    async () => {

        if (!hasNativeApi) {
            document.getElementById("output").textContent =
                "Save As requires the desktop app (run via desktop.py), " +
                "not a plain browser tab.";
            return;
        }

        const script =
            document.getElementById("script").value;

        const result =
            await window.pywebview.api.save_file_as(script);

        if (!result) {
            return;
        }

        if (result.error) {
            document.getElementById("output").textContent =
                "Error saving file: " + result.error;
            return;
        }

        setCurrentFile(
            result.path,
            result.path.split("/").pop()
        );

        document.getElementById("output").textContent =
            `Saved: ${currentFileName}`;
    }
);


// ------------------------------------------------------------
// NATIVE BRIDGE READY
// ------------------------------------------------------------

// window.pywebview only exists once this fires -- it's not available
// on normal page load, per pywebview's own docs.
window.addEventListener(
    "pywebviewready",
    () => {
        hasNativeApi = true;
    }
);
