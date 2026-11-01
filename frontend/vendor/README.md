# Vendored front-end libraries

These are shipped inside the app (no CDN) so the viewer and editor work
offline and a compromised third-party host can't inject code into a page that
can run Python. Upstream files, unmodified (except `fonts/fonts.css`, written for this project):

| Library | Version | Licence | Files |
|---|---|---|---|
| three.js | 0.180.0 | MIT | `build/three.module.min.js`, `build/three.core.min.js`, `examples/jsm/controls/OrbitControls.js`, `examples/jsm/loaders/STLLoader.js` |
| CodeMirror | 5.65.16 | MIT | `lib/codemirror.js`, `lib/codemirror.css`, `theme/material-darker.css`, `mode/python/python.js` |
| IBM Plex Sans / Mono | 5.3.0 (@fontsource) | SIL OFL 1.1 | `fonts/*.woff2` (latin 400/500/600), `fonts/fonts.css` |

Licence texts: `three/LICENSE`, `codemirror/LICENSE`, `fonts/LICENSE-OFL.txt`.

To upgrade, download the same files from the npm packages (`npm pack
three@X codemirror@Y`), replace them here, and bump the versions above and in
`CHANGELOG.md`.
