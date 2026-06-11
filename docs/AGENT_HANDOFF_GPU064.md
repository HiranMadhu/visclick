# Agent handoff — running experiments on us01odc-sc4-1-gpu064

This document is a one-shot brief for a fresh Cursor agent running on
`us01odc-sc4-1-gpu064`. The parallel agent on `us01odcvde74870` (CPU edit
host) wrote this. Two agents now share the project: this one drives
training; the other drives code/doc edits. They coordinate through Git.

## Identity

- **Project:** VisClick — MSc dissertation, GUI element detection + click.
- **Owner:** Hiran Madhu (user `madhus`).
- **GitHub repo:** `https://github.com/HiranMadhu/visclick.git` (public).
- **Repo workspace on shared FS (likely visible from here too):**
  `/remote/edageuclidevhdlbm1/hiran/RTLAssistent/8-CodeAgent/11-AprilBuild/4-case/gui_temp/visclick`

## Open the SSH connection

From a local Cursor window (or terminal):

```bash
# Plain SSH login, if you only want a shell:
ssh madhus@us01odc-sc4-1-gpu064

# Cursor Remote-SSH:
# 1. Cmd/Ctrl + Shift + P  ->  "Remote-SSH: Connect to Host..."
# 2. Type:  madhus@us01odc-sc4-1-gpu064   (or add to ~/.ssh/config first)
# 3. Once connected, File -> Open Folder -> pick the workspace
```

Suggested `~/.ssh/config` block (on your local laptop):

```ssh-config
Host visclick-gpu
    HostName us01odc-sc4-1-gpu064
    User madhus
    ForwardAgent yes
    ServerAliveInterval 60
    ServerAliveCountMax 5
```

Then just `ssh visclick-gpu` or pick `visclick-gpu` in Cursor's host list.

If SSH refuses with `Permission denied (publickey, gssapi-keyex,
gssapi-with-mic, password)`, the box is configured for key-only auth from
trusted hosts. Drop your laptop's public key into
`~/.ssh/authorized_keys` on gpu064 (via Jumphost or your IT-managed key
service), then retry.

## What workspace to open in Cursor on gpu064

Two clean options. Prefer (a) if you have time to verify, otherwise (b).

**(a) Reuse the shared workspace** — if `/remote/edageuclidevhdlbm1/...`
is NFS-mounted on gpu064, both agents see the same files, no clone needed:

```bash
ls /remote/edageuclidevhdlbm1/hiran/RTLAssistent/8-CodeAgent/11-AprilBuild/4-case/gui_temp/visclick/scripts/run_ssp_local.py
```

If that prints the path (not an error), open this folder in Cursor:

```
/remote/edageuclidevhdlbm1/hiran/RTLAssistent/8-CodeAgent/11-AprilBuild/4-case/gui_temp/visclick
```

**(b) Fresh clone on local disk** — if the share is not mounted, or you
want isolation:

```bash
mkdir -p ~/code && cd ~/code
git clone https://github.com/HiranMadhu/visclick.git
cd visclick
git pull --rebase origin main
```

Open `~/code/visclick` in Cursor.

## Kickoff prompt for the gpu064 agent

Paste this as the first message to the agent in the gpu064 Cursor window.

```
You are running on us01odc-sc4-1-gpu064 as user madhus. This workspace is
the VisClick MSc project. Read these in order before doing anything:

  1. docs/AGENT_HANDOFF_GPU064.md   <-- your context (this file)
  2. docs/RUN_ON_LOCAL_GPU.md       <-- step-by-step runbook
  3. scripts/run_ssp_local.py       <-- the script you will execute

Goal: complete D-02 (SimSiam SSP pretraining) for the dissertation,
producing weights/ssp/backbone_simsiam.pt and reports/tables/ssp_loss_log.csv.

Boundaries:
  - You own: training, env setup, data staging, results.
  - You do NOT own: editing notebooks, editing docs (other than this one),
    or refactoring the script. If you spot bugs, report them; the edit-host
    agent will fix and push.
  - Push permission: ASK ME before pushing. Default is "commit locally,
    report the commit hash, I'll push from the other window."

Procedure:
  Phase A - discovery. Run and report:
    hostname && whoami
    nvidia-smi -L
    python3 --version
    git rev-parse --short HEAD
    find /remote -maxdepth 6 -name "unified"              -type d 2>/dev/null | head
    find /remote -maxdepth 6 -name "source_train_bundles" -type d 2>/dev/null | head
    find /remote -maxdepth 6 -name "best_source_v8s.pt"   2>/dev/null | head
  Stop after Phase A and wait for confirmation on data paths.

  Phase B - env. Follow runbook section 4 (create venv, install torch with
  the correct CUDA wheel, install ultralytics + deps). Print the post-install
  `python -c "import torch; print(torch.cuda.is_available(), ...)"` line.

  Phase C - smoke test. Set $VISCLICK_DATA appropriately, then:
    python scripts/run_ssp_local.py --epochs 1 --max-corpus 200
  Confirm the first epoch completes and a checkpoint lands in
  $VISCLICK_DATA/weights/ssp/.

  Phase D - full run.
    python scripts/run_ssp_local.py
  10 epochs, ~15-25 min on a modern GPU. If interrupted, just re-run the
  same command; the script auto-resumes.

  Phase E - publish.
    cp $VISCLICK_DATA/weights/ssp/ssp_loss_log.csv \
       reports/tables/ssp_loss_log.csv
    git add reports/tables/ssp_loss_log.csv
    git -c user.email=madhus@... -c user.name="Hiran Madhu" \
        commit -m "D-02: SimSiam SSP loss log (gpu064 run)"
    git rev-parse --short HEAD       # report this hash
  Also copy backbone_simsiam.pt to a durable location I name; do NOT add
  the .pt to git.

After each phase, summarise outputs and pause for confirmation before
moving to the next phase.
```

## State of the project as of this handoff

- **Pull latest** (`git pull --rebase origin main`) before any run.
- **D-01** DETR — DONE.
- **D-02** SSP — DONE (Colab; `ssp_loss_log.csv`, `ssp_few_shot.csv` in git).
- **D-03 / D-04** — Colab GPU quota exhausted; **run on this box** via:
  - `scripts/setup_visclick_data.sh` — wget Zenodo unified bundle
  - `scripts/run_uda_at_local.py` — D-03 Adaptive Teacher
  - `scripts/run_uda_shot_local.py` — D-04 SHOT
- **Still need manually:** `best_source_v8s.pt` (~22 MB) under
  `$VISCLICK_DATA/weights/baseline_source/` (scp from Colab Drive or laptop).

## Quick start on gpu064 (D-03 then D-04)

```bash
cd /remote/edageuclidevhdlbm1/hiran/RTLAssistent/8-CodeAgent/11-AprilBuild/4-case/gui_temp/visclick
git pull --rebase origin main

export VISCLICK_DATA=$HOME/visclick_data
bash scripts/setup_visclick_data.sh          # ~10-30 min first time (Zenodo wget)

# one-time venv (if not already created):
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip wheel
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install ultralytics datasets pillow opencv-python matplotlib onnx onnxruntime onnxslim

# verify GPU:
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"

# place best_source_v8s.pt (see MISSING line from setup script), then:
python scripts/run_uda_at_local.py --data-root "$VISCLICK_DATA"
python scripts/run_uda_shot_local.py --data-root "$VISCLICK_DATA"

# commit results (ask before push):
git add reports/tables/uda_adaptive_teacher.csv reports/tables/uda_shot.csv
git commit -m "D-03/D-04: UDA results (gpu064 run)"
```

## Coordination ground rules

- **Git is the contract.** When the gpu064 agent commits, it reports the
  hash; the edit-host agent fetches and pushes. When the edit-host agent
  pushes, the gpu064 agent pulls before its next run.
- **File ownership to avoid merge pain:**
  - Edit-host owns: `docs/*` (except this file), `notebooks/*`,
    `scripts/*` (except `run_*_local.py` improvements that gpu064
    proposes), `Final_Report_v2.md`.
  - gpu064 owns: `reports/tables/ssp_*`, `weights/ssp/*` (data only, not
    in git), and may edit this file (`AGENT_HANDOFF_GPU064.md`) to add
    observed-state notes.
- **Tokens.** The `token` file in the repo contains a GitHub PAT. Do not
  echo it to chat or commit it. If push permission is granted, the agent
  reads it via `git push https://USER:$(cat token)@github.com/...`.
- **Reporting back.** Every meaningful step should end with a one-line
  `REPORT ...` summary in the agent's output, matching the convention
  used in the notebooks. Easier for the human to skim.

## Quick commands the gpu064 agent will use

```bash
# Sync the repo on entry / between hand-offs:
git -C $(git rev-parse --show-toplevel) fetch origin
git -C $(git rev-parse --show-toplevel) reset --hard origin/main

# Check on a long-running training without re-running:
tail -F $VISCLICK_DATA/weights/ssp/ssp_loss_log.csv

# Force a clean restart (deletes prior checkpoint):
python scripts/run_ssp_local.py --force-fresh

# Smaller-GPU fallback (if 8GB or less):
python scripts/run_ssp_local.py --batch 32 --workers 2
```
