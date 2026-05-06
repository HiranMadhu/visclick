# Template reference PNGs for Phase 1.C.1 baseline

`scripts/baseline_template.py` looks up reference PNGs in this directory by
filename. Each task in `tasks/T01_T20.json` declares a `target_template`
field (e.g. `Save.png`); if the file is missing, the template baseline
records "template not found" and the task counts as a miss for that
method (this is realistic — SikuliX-style tools are blind to controls
they have not seen before).

## How to capture a template (one-time, ~20 seconds per template)

1. Open the target app and bring it to the state described in the task's
   `setup` field (e.g. for **T01** open Notepad and trigger Save As).
2. Press `Win + Shift + S` to launch the Windows Snipping Tool.
3. Choose **Rectangular Snip** and tightly crop the control. Aim for:
   - At least 24x24 pixels (smaller templates have too few features for
     `cv2.matchTemplate` to discriminate).
   - Tight margins: do NOT include surrounding chrome, hover effects, or
     the cursor.
4. The snip lands in the clipboard. Paste it into Paint / IrfanView /
   any image editor and **Save As** PNG with the exact filename the task
   declares. Save here (`samples/templates/`).

## Required templates for the canonical task list

The current `tasks/T01_T20.json` references these filenames:

| Task | Filename                       | Description                              |
|------|--------------------------------|------------------------------------------|
| T01  | `Save.png`                     | Notepad Save-As "Save" button            |
| T02  | `File_menu.png`                | Notepad menubar "File" item              |
| T03  | `VSCode_Search.png`            | VS Code activity-bar Search icon         |
| T05  | `VSCode_SettingsSearch.png`    | VS Code Settings page search box         |
| T06  | `Explorer_View.png`            | File Explorer ribbon "View" tab          |
| T07  | `Properties.png`               | Right-click context menu "Properties"    |
| T08  | `Explorer_Addr.png`            | File Explorer address bar                |
| T09  | `Chrome_Omnibox.png`           | Chrome address-and-search bar            |
| T10  | `Chrome_ClearBrowsing.png`     | Chrome Settings → Privacy → Clear button |
| T13  | `VSCode_Commit.png`            | VS Code Source Control "Commit" button   |
| T15  | `Save.png`                     | Same as T01 (negative case — should miss)|

Tasks **T04, T11, T12, T14** intentionally have `target_template = ""` —
they exercise targets the template baseline cannot represent (positional
or text-inside-text). They will count as misses for the template method,
which is the correct behaviour to record.

## Template files are NOT committed by default

`.gitignore` is unchanged; PNGs in this directory are local artefacts.
Capturing them takes the same time on any reviewer's machine, and the
exact pixels depend on theme/scale/version. If you do want to commit
your captures (for a frozen reproducibility snapshot), explicitly
`git add -f samples/templates/<name>.png`.
