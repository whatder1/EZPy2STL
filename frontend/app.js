import * as THREE from
    'https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js';

import { OrbitControls } from
    'https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/controls/OrbitControls.js';

import { STLLoader } from
    'https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/loaders/STLLoader.js';

import { parseParams, formatParamLabel, formatParamLine } from
    './params.js';


// ------------------------------------------------------------
// SCRIPT EDITOR (CodeMirror)
//
// Replaces the plain #script textarea with a syntax-highlighted,
// line-numbered editor. CodeMirror is loaded as classic <script> tags
// in index.html (not an ES module -- v5 doesn't ship one), so the
// global `CodeMirror` is already available by the time this module
// runs (module scripts execute after the document is parsed).
//
// CodeMirror.fromTextArea() hides the original textarea and keeps it
// in the DOM as a sync target, but doesn't keep its .value live-
// updated in real time -- so every other place in this file that used
// to read/write the textarea's .value now goes through these two
// functions instead.
// ------------------------------------------------------------

const editor =
    CodeMirror.fromTextArea(
        document.getElementById("script"),
        {
            mode: "python",
            theme: "material-darker",
            lineNumbers: true,
            indentUnit: 4,
            tabSize: 4,
            indentWithTabs: false
        }
    );


function getScriptText() {
    return editor.getValue();
}


function setScriptText(text) {
    editor.setValue(text);
}


// CodeMirror caches its own layout measurements and doesn't notice
// when its container is resized by something else (dragging a panel
// divider, resizing the window) -- this keeps it in sync whenever
// that happens, instead of sprinkling editor.refresh() calls into
// every place that can change its size.
new ResizeObserver(() => editor.refresh())
    .observe(editor.getWrapperElement());


// Editor starts blank -- open a file or write your own script.


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

// Catches the viewer resizing for reasons other than the OS window
// changing size -- specifically, dragging the panel divider below.
// A plain "resize" event on window doesn't fire for that.
new ResizeObserver(resizeViewer).observe(
    document.getElementById("viewer")
);


// ------------------------------------------------------------
// PANEL DIVIDER (drag to resize the script/viewer split)
// ------------------------------------------------------------

const divider =
    document.getElementById("divider");

const leftPanel =
    document.getElementById("left");

const layoutEl =
    document.getElementById("layout");

let draggingDivider = false;

divider.addEventListener(
    "mousedown",
    (event) => {
        draggingDivider = true;
        divider.classList.add("dragging");
        document.body.style.cursor = "col-resize";
        document.body.style.userSelect = "none";
        event.preventDefault();
    }
);

window.addEventListener(
    "mousemove",
    (event) => {

        if (!draggingDivider) {
            return;
        }

        const layoutRect =
            layoutEl.getBoundingClientRect();

        const minLeft = 320;
        const minRight = 320;

        let newWidth =
            event.clientX - layoutRect.left;

        newWidth = Math.max(
            minLeft,
            Math.min(
                newWidth,
                layoutRect.width - minRight - divider.offsetWidth
            )
        );

        leftPanel.style.width = newWidth + "px";
    }
);

window.addEventListener(
    "mouseup",
    () => {

        if (!draggingDivider) {
            return;
        }

        draggingDivider = false;
        divider.classList.remove("dragging");
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
    }
);


// ------------------------------------------------------------
// VERTICAL DIVIDERS (params <-> script, script <-> console)
// ------------------------------------------------------------

function makeVerticalResizer(dividerEl, targetEl, options) {

    let dragging = false;
    let startY = 0;
    let startHeight = 0;

    const {
        grows, // "down" if dragging down grows targetEl, "up" if dragging up grows it
        min,
        max
    } = options;

    dividerEl.addEventListener(
        "mousedown",
        (event) => {
            dragging = true;
            startY = event.clientY;
            startHeight = targetEl.getBoundingClientRect().height;
            dividerEl.classList.add("dragging");
            document.body.style.cursor = "row-resize";
            document.body.style.userSelect = "none";
            event.preventDefault();
        }
    );

    window.addEventListener(
        "mousemove",
        (event) => {

            if (!dragging) {
                return;
            }

            const delta =
                grows === "down"
                    ? event.clientY - startY
                    : startY - event.clientY;

            const newHeight =
                Math.max(min, Math.min(max, startHeight + delta));

            targetEl.style.maxHeight = newHeight + "px";
            targetEl.style.height = newHeight + "px";
        }
    );

    window.addEventListener(
        "mouseup",
        () => {

            if (!dragging) {
                return;
            }

            dragging = false;
            dividerEl.classList.remove("dragging");
            document.body.style.cursor = "";
            document.body.style.userSelect = "";
        }
    );
}


// Dragging down grows the Parameters panel (pushes into the script area).
makeVerticalResizer(
    document.getElementById("params-divider"),
    document.getElementById("params"),
    { grows: "down", min: 60, max: 600 }
);

// Dragging the console divider UP grows the output console (pushes up
// into the script area) -- dragging down shrinks it back.
makeVerticalResizer(
    document.getElementById("console-divider"),
    document.getElementById("output"),
    { grows: "up", min: 60, max: 600 }
);

// Dragging the files divider UP grows the generated-files list (pushes
// up into the script area) -- dragging down shrinks it back. #files
// has its own overflow-y: auto, so anything past the current height
// scrolls instead of being clipped.
makeVerticalResizer(
    document.getElementById("files-divider"),
    document.getElementById("files"),
    { grows: "up", min: 60, max: 600 }
);


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

function renderFileList(names, group, activeScope) {

    // activeScope is the outer #files panel (which may contain both
    // the stl and other-formats groups) -- selectFile needs it to
    // clear "active" off a row in the *other* group, not just this
    // one. Falls back to group itself so existing single-group calls
    // still work.
    const scope =
        activeScope || group;

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
            () => selectFile(name, scope)
        );


        let downloadEl;

        if (hasNativeApi) {

            downloadEl =
                document.createElement("button");

            downloadEl.className = "file-download file-download-btn";
            downloadEl.textContent = "Download";

            downloadEl.addEventListener(
                "click",
                () => downloadNative(name, downloadEl)
            );

        } else {

            // Browser-only fallback. Not used when running the actual
            // desktop app -- see downloadNative() for why.
            downloadEl =
                document.createElement("a");

            downloadEl.className = "file-download";

            downloadEl.href =
                "/download/" + encodeURIComponent(name);

            downloadEl.textContent = "Download";

            downloadEl.download =
                name.split("/").pop();
        }


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
        actions.appendChild(downloadEl);


        row.appendChild(nameButton);
        row.appendChild(actions);
        group.appendChild(row);
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


async function downloadNative(name, button) {

    const originalText =
        button.textContent;

    button.textContent = "Saving...";

    button.disabled = true;

    try {

        const result =
            await window.pywebview.api.download_file(name);

        if (!result) {
            // Dialog was cancelled -- not an error.
            return;
        }

        if (result.error) {
            throw new Error(result.error);
        }

        button.textContent = "Saved!";

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

    if (name.toLowerCase().endsWith(".stl")) {

        await loadModel(name);

    } else {

        // No loader for STEP/3MF in this viewer -- download or send
        // to OrcaSlicer instead, both of which already work for any
        // format via the existing per-row buttons.
        document.getElementById("output").textContent =
            `Preview not available for ${name} -- use Download or ` +
            `Open in OrcaSlicer instead.`;
    }

    for (const row of panel.querySelectorAll(".file-row")) {

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
// form controls. Editing a control rewrites that exact line via
// setScriptText() -- the editor stays the single source of truth,
// this is just a friendly editor bound to specific lines in it.
// (Parsing/formatting logic itself lives in params.js, imported
// above, so it's testable outside a browser.)
// ------------------------------------------------------------

function writeParamValue(param, newValue) {

    const lines =
        getScriptText().split("\n");

    lines[param.lineIndex] =
        formatParamLine(param, newValue);

    setScriptText(lines.join("\n"));
}


function renderParamsPanel() {

    const panel =
        document.getElementById("params");

    const params =
        parseParams(getScriptText());

    panel.innerHTML = "";

    document.getElementById("params-divider").style.display =
        params.length ? "" : "none";

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
// and (debounced) as the person types directly in the editor. Autosave
// piggybacks on the same change event with its own, longer debounce.

let paramRefreshTimer = null;

function scheduleParamRefresh() {

    clearTimeout(paramRefreshTimer);

    paramRefreshTimer =
        setTimeout(renderParamsPanel, 400);
}

editor.on(
    "change",
    () => {
        scheduleParamRefresh();
        scheduleAutosave();
    }
);

// Initial render of the (empty) params panel for the blank editor.
renderParamsPanel();


// ------------------------------------------------------------
// BUILD
// ------------------------------------------------------------

async function build() {

    const buildButton =
        document.getElementById("build-button");

    const script =
        getScriptText();

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

            // STLs first, STEP/3MF grouped separately below (hidden
            // by default behind the "Show STEP / 3MF" toggle).
            const stlFiles =
                result.files.filter(
                    f => f.toLowerCase().endsWith(".stl")
                );

            const otherFiles =
                result.files.filter(
                    f => !f.toLowerCase().endsWith(".stl")
                );

            if (stlFiles.length > 0) {

                const stlGroup =
                    document.createElement("div");

                stlGroup.className = "file-group";

                renderFileList(stlFiles, stlGroup, filesPanel);
                filesPanel.appendChild(stlGroup);
            }

            if (otherFiles.length > 0) {

                const otherGroup =
                    document.createElement("div");

                otherGroup.className = "file-group file-group-other";

                renderFileList(otherFiles, otherGroup, filesPanel);
                filesPanel.appendChild(otherGroup);
            }

            // Auto-load an STL if one was produced (previewable);
            // otherwise fall back to just the first file in the list.
            const initialFile =
                result.files.find(f => f.toLowerCase().endsWith(".stl")) ||
                result.files[0];

            await selectFile(
                initialFile,
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
// AUTOSAVE (crash/close recovery)
//
// Periodically POSTs the current script to the backend, which writes
// it to a recovery file outside the actual project files. On next
// launch, if a recovery copy exists, a banner offers to restore it --
// never silently, since that could clobber an intentional blank start.
// ------------------------------------------------------------

let autosaveTimer = null;

function scheduleAutosave() {

    clearTimeout(autosaveTimer);

    autosaveTimer = setTimeout(
        async () => {
            try {
                await fetch("/autosave", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ script: getScriptText() })
                });
            } catch (error) {
                // Non-critical -- don't interrupt the person's work
                // over a failed autosave write.
                console.error("Autosave failed:", error.message);
            }
        },
        2000
    );
}


async function clearAutosave() {

    clearTimeout(autosaveTimer);

    try {
        await fetch("/autosave", { method: "DELETE" });
    } catch (error) {
        console.error("Could not clear autosave:", error.message);
    }
}


async function checkForRecovery() {

    let data;

    try {
        const response = await fetch("/autosave");
        data = await response.json();
    } catch (error) {
        return;
    }

    if (!data.content || !data.content.trim()) {
        return;
    }

    const banner =
        document.getElementById("recovery-banner");

    banner.classList.add("visible");

    document
        .getElementById("recovery-restore")
        .addEventListener(
            "click",
            () => {
                setScriptText(data.content);
                renderParamsPanel();
                banner.classList.remove("visible");
            },
            { once: true }
        );

    document
        .getElementById("recovery-discard")
        .addEventListener(
            "click",
            async () => {
                await clearAutosave();
                banner.classList.remove("visible");
            },
            { once: true }
        );
}

checkForRecovery();


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

    setScriptText(text);

    renderParamsPanel();

    setCurrentFile(path || null, name || null);

    document.getElementById("recovery-banner").classList.remove("visible");

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


// ------------------------------------------------------------
// RECENT FILES
// ------------------------------------------------------------

const recentToggle =
    document.getElementById("recent-toggle");

const recentDropdown =
    document.getElementById("recent-dropdown");


async function openRecentPath(path) {

    const result =
        await window.pywebview.api.open_recent(path);

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


async function refreshRecentDropdown() {

    if (!hasNativeApi) {
        return;
    }

    const files =
        await window.pywebview.api.get_recent_files();

    recentDropdown.innerHTML = "";

    if (!files.length) {

        const empty =
            document.createElement("div");

        empty.className = "recent-empty";
        empty.textContent = "No recent files yet";

        recentDropdown.appendChild(empty);
        return;
    }

    for (const file of files) {

        const item =
            document.createElement("button");

        item.className = "recent-item";
        item.textContent = file.name;
        item.title = file.path;

        item.addEventListener(
            "click",
            () => {
                recentDropdown.classList.remove("visible");
                openRecentPath(file.path);
            }
        );

        recentDropdown.appendChild(item);
    }
}


recentToggle.addEventListener(
    "click",
    async (event) => {

        event.stopPropagation();

        const opening =
            !recentDropdown.classList.contains("visible");

        if (opening) {
            await refreshRecentDropdown();
        }

        recentDropdown.classList.toggle("visible", opening);
    }
);

// Click anywhere else closes the dropdown.
window.addEventListener(
    "click",
    () => {
        recentDropdown.classList.remove("visible");
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
            getScriptText();

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

        clearAutosave();

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
            getScriptText();

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

        clearAutosave();

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

// window.pywebview only exists once the bridge is ready, per
// pywebview's own docs -- but the "pywebviewready" event can fire
// before this script finishes registering the listener below (a race
// that got more likely once CodeMirror's blocking CDN <script> tags
// started delaying how soon this module runs). So: check directly
// first for the case where it already fired, and still listen for the
// case where it hasn't yet.

function markNativeApiReady() {
    hasNativeApi = true;
}

if (window.pywebview) {
    markNativeApiReady();
} else {
    window.addEventListener("pywebviewready", markNativeApiReady);
}
