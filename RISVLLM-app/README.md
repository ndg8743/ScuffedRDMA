 RISVLLM-App: Reverse Engineering IDE                                                         
                                                                                           
 Context

 Build a full-stack decompilation IDE web app inside ScuffedRDMA/RISVLLM-app/. The
 LLM4Decompile-22b-v2 model (22B params, BF16, ~44GB VRAM) runs on Cerberus (2x RTX 5090,
 TP=2) via vLLM. The web app runs as a K8s pod on Chimera (no GPU needed). Includes an
 embedded RISC-V emulator via custom TinyEMU WASM build.

 Architecture

 [Browser] → [Traefik] → [RISVLLM Pod on Chimera:3000]
                               ├── React Frontend (Monaco, xterm.js, TinyEMU WASM)
                               └── Express Backend → [vLLM on Cerberus:8000]

 Step 1: Clone repo & download model on Cerberus

 - Clone ScuffedRDMA to ~/ScuffedRDMA
 - SSH to Cerberus, create /data/models, download llm4decompile-22b-v2 via huggingface-cli
 - Verify model files on disk

 Step 2: Deploy vLLM on Cerberus

 - K8s Deployment: vLLM serving llm4decompile-22b-v2 with TP=2, runtimeClassName: nvidia
 - Service exposing port 8000 (OpenAI-compatible API)
 - Node selector: cerberus
 - Mount /data/models as hostPath

 Step 3: Scaffold RISVLLM-app

 ScuffedRDMA/RISVLLM-app/
 ├── frontend/
 │   ├── src/
 │   │   ├── App.jsx
 │   │   ├── main.jsx
 │   │   ├── index.css
 │   │   ├── components/
 │   │   │   ├── Layout.jsx          # IDE shell with resizable panels
 │   │   │   ├── Sidebar.jsx         # Nav: Decompile, Emulator, Terminal
 │   │   │   ├── EditorPanel.jsx     # Monaco editor (assembly input)
 │   │   │   ├── OutputPanel.jsx     # Monaco editor (C output, read-only)
 │   │   │   ├── DiffView.jsx        # Side-by-side diff of input/output
 │   │   │   ├── UploadWizard.jsx    # Multi-step: upload binary / paste code / set O-level
 │   │   │   ├── EmulatorModal.jsx   # TinyEMU WASM RISC-V in popup window
 │   │   │   ├── TerminalPanel.jsx   # xterm.js terminal
 │   │   │   ├── StatusBar.jsx       # Bottom bar: connection status, model info
 │   │   │   └── Header.jsx          # Top bar: RISVLLM branding
 │   │   └── lib/
 │   │       ├── api.js              # Backend API client
 │   │       └── tinyemu/            # TinyEMU WASM assets
 │   ├── public/
 │   │   └── tinyemu/               # WASM binary + RISC-V disk images
 │   ├── index.html
 │   ├── vite.config.js
 │   ├── tailwind.config.js
 │   └── package.json
 ├── backend/
 │   ├── server.js                   # Express entry point
 │   ├── routes/
 │   │   ├── decompile.js            # POST /api/decompile — proxy to vLLM
 │   │   ├── upload.js               # POST /api/upload — binary upload + Ghidra processing
 │   │   └── health.js               # GET /api/health
 │   ├── lib/
 │   │   └── vllm-client.js          # vLLM OpenAI-compatible API client
 │   └── package.json
 ├── Dockerfile                      # Multi-stage: build frontend, serve with Node
 ├── k8s/
 │   ├── deployment.yaml             # Web app pod on Chimera
 │   ├── service.yaml                # ClusterIP service
 │   ├── ingress.yaml                # Traefik IngressRoute
 │   └── vllm-cerberus.yaml          # vLLM deployment on Cerberus
 └── README.md

 Step 4: Build backend

 - POST /api/decompile — accepts { code, optimizationLevel, inputType }, formats prompt for
 llm4decompile, calls vLLM, returns C code
 - POST /api/upload — accepts binary file upload via multer, extracts assembly (future:
 Ghidra headless), returns pseudo-code
 - GET /api/health — checks vLLM connectivity
 - vLLM client uses OpenAI-compatible chat/completions endpoint on Cerberus


 Step 5: Build frontend

 - IDE Layout: Dark theme, resizable split panels (allotment or react-resizable-panels)
 - Upload Wizard (Option C):
   a. Choose input: Upload binary OR paste assembly/pseudo-code
   b. Select optimization level: O0, O1, O2, O3
   c. Review input with syntax highlighting
   d. Submit → streaming decompilation output
 - Editor Panels: Monaco Editor — left (input assembly, editable), right (output C,
 read-only)
 - Diff View: Toggle to see side-by-side diff between input and output
 - Emulator Modal: Full-screen popup with TinyEMU WASM running RISC-V Linux (Buildroot)
 - Terminal Panel: xterm.js at bottom (collapsible)
 - Status Bar: Model status, latency, token count

 Step 6: TinyEMU WASM integration

 - Clone TinyEMU source, build WASM target with Emscripten
 - Bundle RISC-V Buildroot disk image (~30MB)
 - Embed in EmulatorModal as canvas + JS bridge
 - Users can compile C code in emulated RISC-V Linux, test binaries

 Step 7: Containerize & deploy

 - Multi-stage Dockerfile: Node 18 builds frontend (vite build), then serves static + backend
 - K8s manifests: Deployment (nodeSelector: chimera), Service, IngressRoute
 - Build image, import to RKE2 containerd on Chimera
 - Deploy vLLM pod on Cerberus first, then web app on Chimera

 Step 8: Verify

 - curl vLLM health endpoint on Cerberus
 - curl web app health endpoint on Chimera
 - Open browser, test decompile flow end-to-end
 - Test emulator popup launches RISC-V Linux
 - Test from external network

 Key Decisions

 - TinyEMU custom WASM over JSLinux iframe (full control, self-hosted, matches IDE aesthetic)
 - Option C wizard for multi-step input with optimization level selection
 - Monaco Editor for VS Code-quality code editing
 - vLLM with TP=2 on Cerberus for the 22B model across both 5090s
 - No GPU needed for web app pod on Chimera
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌