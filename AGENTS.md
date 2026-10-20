# RigAndBone2D agent instructions

Read README.md and docs/AGENT_API.md before operating the application.
For rig authoring, use scripts/agent.py or the binary's --agent JSONL interface. Inspect before editing. Check every response's ok field. Render and visually inspect authored poses before exporting. Use a single writer per project. Use expected_revision for stale edit detection. Do not modify the reference video.

For development, keep changes in the responsible module. Preserve the shared ProjectCore validation, sampler and renderer for GUI and API workflows. Build with ./scripts/build-app.sh, then run python3 tests/agent_smoke.py. The app targets macOS 14+ and Apple Silicon. Mesh deformation is currently unsupported; do not claim rigid sprites implement it.

For new characters, read docs/AGENT_WORKFLOW.md and use scripts/rig_pipeline.py with versioned recipes. Prefer stable bone IDs, apply_recipe and atomic batch edits. Use the shared SDK in scripts/rigtools/client.py; reuse revision receipts and surface conflicts without silently retrying. Prepare and preview into a new job directory. Review quality-report.json and visually inspect key poses before delivery.

For changes to these workflows, also run tests/agent_workflow.py, tests/render_orientation.py and tests/demo_reproducibility.py. The last two need Pillow. Preserve the original demo projects; reproduction tests build into temporary directories. Do not delete active project lock sidecars. Project persistence belongs in ProjectStore, not directly in UI or transport code.

For Godot handoff, read docs/GODOT_HANDOFF.md. Keep generated character resources separate from gameplay scripts. Do not ship source sheets, rig projects, previews or revision archives as runtime assets. Run tests/godot_bridge.py for bridge changes. Report disk bytes and RGBA8 estimates separately; do not claim measured FPS/GPU memory from atlas dimensions alone.

## LumioValley collaboration (ADR-014)
For LumioValley tasks, all agents may author tools, prompts, assets, rigs, integration and documentation within claimed task scopes. Follow ../LumioValley/AGENTS.md and ../LumioValley/docs/AGENT_WORKFLOW.md for task packets and handoffs. Roles are not model-specific. Preserve this project's single-writer rig ownership, expected_revision safeguards and technical validation above. Parallel work must use disjoint path groups and avoid shared build/export/rig resources; do not edit one rig project concurrently. No autonomous delegation is required. These collaboration rules apply to LumioValley work; other consumers keep their own project contracts.

<!-- pstack:begin -->
## Mandatory Operating Mode: `poteto-mode` (`pstack` Low/Medium Anti-Overthinking Standard)

You MUST operate in **`poteto-mode` (`pstack`)** by default on every task without waiting for the user to type `/poteto-mode`:

0. **Mandatory Visible Badge & Step-1 Skill Load (Non-Negotiable)**:
   - **Always start your response** with a 1-line status badge declaring the active `poteto-mode` playbook and skill:
     `⚡ **[poteto-mode / pstack: <Playbook or Skill Name>]**` (e.g., `⚡ **[poteto-mode / pstack: feature + model-the-domain]**`, `⚡ **[poteto-mode / pstack: perf-issue + benchmark-checklist]**`, or `⚡ **[poteto-mode / pstack: investigation + how/architect]**`).
   - **Step 1 Action**: On any non-trivial task, immediately load/read the matched `poteto-mode` playbook or `pstack` skill (`poteto-mode`, `how`, `why`, `architect`, `blast-radius`, `tdd`, `benchmark-checklist`) before editing or concluding.
1. **Action-First, Zero Overthinking (Low/Medium Mode Native)**:
   - Respect the active **Low or Medium** reasoning setting (`inherit-parent` / `auto`). Never escalate effort to `high`, `xhigh`, or `max`.
   - Prefer immediate tool calls (read file, run command/test, measure real state) over internal speculation.
   - Scale workflow ceremony to task size: execute small or direct edits immediately via **Laziness Protocol** + **Prove It Works** without spawning unnecessary multi-model panels.
2. **Core `poteto-mode` Engineering Principles (Always Active)**:
   - **Laziness Protocol & Subtract First**: Delete dead weight before adding code. Ship the smallest, cleanest change that solves the root cause.
   - **Model the Domain & Fix Root Causes**: Name the data shape first. Trace bugs to the first place state went wrong; never paper over bugs with speculative guards.
   - **Prove It Works & Explain the Number**: Never claim done from "it compiles" or self-report. Verify against the real artifact/test/UI readback, and label every claim or metric as *measured*, *inferred*, or *guess*.
   - **Never Block on the Human**: If a fork can be settled by reading code, running a command, or a quick prototype, test it yourself. Pause only for irreversible actions (data deletion, force-push, external publish) or genuine product/design conflicts (e.g., spec vs legacy rule).
   - **Unslop & No-Comments**: Write concise, direct responses (no AI filler). Write self-explanatory code with zero narration comments (`// Step 1...`); keep comments only for non-obvious external constraints.
3. **Automatic Playbook & Skill Router (Match & Load on Step 1)**:
   - **System analysis / Planning / Architecture ("วิเคราะห์ระบบ", "วางแผน", "ออกแบบ")** -> `poteto-mode` (`investigation.md` + `how` / `architect`).
   - **Performance / Optimization ("optimize", "ประสิทธิภาพสูงสุด", "ช้า", "คอขวด")** -> `poteto-mode` (`perf-issue.md` + `benchmark-checklist`).
   - **New feature / Feedback update / Refactor ("อัพเดต feedback", "ทำระบบใหม่", "เพิ่มฟีเจอร์", "refactor")** -> `poteto-mode` (`feature.md` or `refactoring.md` + `blast-radius`).
   - **Bug fix / Regression ("แก้บั๊ก", "พัง", "error")** -> `poteto-mode` (`bug-fix.md` + `tdd`: reproduce first -> root-cause -> test & verify).
   - **Frontend / UI Development / Web design ("ทำหน้าเว็บ", "ออกแบบ UI", "สร้างหน้าตา", "dashboard")** -> `poteto-mode` (`feature.md` + ensure `DESIGN.md` exists via `designmd search` + `architect`).
   - **"How does X work?" / "Why is Y like this?"** -> `how` and `why` skills.
   - **Large multi-file sweep / Long autonomous run** -> delegate bulk work to background subagents (`poteto-agent` / `swarm` on `inherit-parent` or `flash`/`medium`) to guard the context window, and log decisions via `show-me-your-work`.
4. **Autonomous UI Design Gate (`DESIGN.md` First)**:
   - When creating or modifying frontend/UI components (HTML, CSS/Tailwind, React, Svelte, Vue), check if `DESIGN.md` exists in the project root.
   - If missing: derive 2-3 domain keywords from user context (e.g., `dark game studio`, `saas dashboard`, `minimal portfolio`), run `designmd search "<keywords>"` or extract from reference URL, and establish `./DESIGN.md` before generating UI code. Adhere strictly to its color tokens, typography, and component specs.
<!-- pstack:end -->
