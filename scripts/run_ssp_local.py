"""Standalone SSP (SimSiam) pretraining for VisClick.

Mirrors notebook 11_ssp_pretrain.ipynb but with no Colab / Drive
dependencies. Configurable through environment variables or CLI flags so it
runs on any Linux box with a GPU.

Typical usage on a local GPU machine:

    export VISCLICK_DATA=/path/to/visclick_data
    # VISCLICK_DATA should contain:
    #   unified/{train,val,test}/images/*.{png,jpg}     (~9k images total)
    #   weights/baseline_source/best_source_v8s.pt      (YOLOv8s source weights)
    #   samples/desktop_seed/*.png                      (50 desktop seeds, optional)
    #   source_train_bundles/{train,val,test}.tar.gz    (OPTIONAL; if present,
    #       use the same image subset notebook 04 selected on Colab)

    python scripts/run_ssp_local.py

Outputs land under $VISCLICK_DATA/weights/ssp/:
    backbone_simsiam.pt    final adapted backbone state dict
    ssp_ckpt.pt            per-epoch checkpoint (model+opt+sched+epoch)
    ssp_loss_log.csv       per-epoch loss curve

Resume is automatic if ssp_ckpt.pt exists with matching EPOCHS target.
Pass --force-fresh to discard prior state and train from epoch 0.

Expected wall-clock on an RTX 30xx / T4 / A100: ~15-30 min for 10 epochs
over ~9k images at batch 64 / imgsz 224.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import tarfile
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as T
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from ultralytics import YOLO


IMG_EXT = (".png", ".jpg", ".jpeg")
CLASSES = ["button", "text", "text_input", "icon", "menu", "checkbox"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data-root", default=os.environ.get("VISCLICK_DATA"),
                   help="Root that contains unified/, source_train_bundles/, weights/, samples/. "
                        "Defaults to $VISCLICK_DATA.")
    p.add_argument("--epochs", type=int, default=10)
    p.add_argument("--batch", type=int, default=64)
    p.add_argument("--img-size", type=int, default=224)
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--force-fresh", action="store_true",
                   help="Delete any prior checkpoint and loss log before training.")
    p.add_argument("--max-corpus", type=int, default=0,
                   help="Cap corpus size (0 = no cap). Useful for smoke tests.")
    return p.parse_args()


def extract_manifest(bundle_path: Path, split: str, cache_dir: Path) -> list[str]:
    out = cache_dir / f"{split}.txt"
    if out.is_file() and out.stat().st_size > 0:
        return [ln.strip() for ln in out.read_text().splitlines() if ln.strip()]
    if not bundle_path.is_file():
        return []
    with tarfile.open(bundle_path, "r:gz") as tf:
        member = next(
            (m for m in tf.getmembers() if m.name.endswith(f"manifests/{split}.txt")),
            None,
        )
        if member is None:
            return []
        out.write_bytes(tf.extractfile(member).read())
    return [ln.strip() for ln in out.read_text().splitlines() if ln.strip()]


def collect_corpus(data_root: Path, max_corpus: int = 0) -> list[str]:
    """Build the SSP corpus from a local data root.

    Two paths to find images:
      1) If `source_train_bundles/<split>.tar.gz` exists, use the manifests
         inside (same set notebook 04 selected on Colab). Reproduces the
         Colab run image-for-image.
      2) Otherwise (typical for a fresh gpu064 setup that wget'd the Zenodo
         bundle directly), list `unified/<split>/images/` and use everything.
         Local filesystems handle directory listing fine, unlike Drive FUSE.
    """
    unified = data_root / "unified"
    bundles = data_root / "source_train_bundles"
    seed = data_root / "samples" / "desktop_seed"

    use_manifests = bundles.is_dir() and any((bundles / f"{sp}.tar.gz").is_file()
                                              for sp in ("train", "val", "test"))
    cache = Path("/tmp/_ssp_manifests_local")
    cache.mkdir(parents=True, exist_ok=True)

    paths: list[str] = []
    for split in ("train", "val", "test"):
        img_dir = unified / split / "images"
        if not img_dir.is_dir():
            print(f"  {split}: image dir missing ({img_dir})")
            continue
        if use_manifests:
            names = extract_manifest(bundles / f"{split}.tar.gz", split, cache)
            if not names:
                print(f"  {split}: manifest empty, falling back to directory listing")
                names = [f.name for f in img_dir.iterdir() if f.suffix.lower() in IMG_EXT]
            paths.extend(str(img_dir / fn) for fn in names)
            print(f"  {split}: {len(names)} paths (from manifest)")
        else:
            names = [f.name for f in img_dir.iterdir() if f.suffix.lower() in IMG_EXT]
            paths.extend(str(img_dir / fn) for fn in names)
            print(f"  {split}: {len(names)} paths (listdir)")

    if seed.is_dir():
        seed_paths = [str(f) for f in seed.iterdir() if f.suffix.lower() in IMG_EXT]
        paths.extend(seed_paths)
        if seed_paths:
            print(f"  desktop_seed: {len(seed_paths)} paths")

    paths = sorted(set(paths))
    if max_corpus and len(paths) > max_corpus:
        paths = paths[:max_corpus]
        print(f"  corpus capped at {max_corpus}")
    return paths


def simsiam_aug(img_size: int) -> T.Compose:
    return T.Compose([
        T.RandomResizedCrop(img_size, scale=(0.5, 1.0)),
        T.RandomHorizontalFlip(p=0.5),
        T.RandomApply([T.ColorJitter(0.4, 0.4, 0.4, 0.1)], p=0.8),
        T.RandomGrayscale(p=0.2),
        T.RandomApply([T.GaussianBlur(kernel_size=23, sigma=(0.1, 2.0))], p=0.5),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


class TwoViewDataset(Dataset):
    def __init__(self, paths: list[str], aug: T.Compose, img_size: int):
        self.paths = paths
        self.aug = aug
        self.img_size = img_size

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, idx: int):
        p = self.paths[idx]
        try:
            with Image.open(p) as im:
                im = im.convert("RGB")
        except Exception:
            im = Image.new("RGB", (self.img_size, self.img_size))
        return self.aug(im), self.aug(im)


class SimSiam(nn.Module):
    def __init__(self, backbone: nn.Module, feat_dim: int,
                 proj_dim: int = 2048, pred_dim: int = 512):
        super().__init__()
        self.backbone = backbone
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.projector = nn.Sequential(
            nn.Linear(feat_dim, proj_dim), nn.BatchNorm1d(proj_dim), nn.ReLU(inplace=True),
            nn.Linear(proj_dim, proj_dim), nn.BatchNorm1d(proj_dim), nn.ReLU(inplace=True),
            nn.Linear(proj_dim, proj_dim), nn.BatchNorm1d(proj_dim, affine=False),
        )
        self.predictor = nn.Sequential(
            nn.Linear(proj_dim, pred_dim), nn.BatchNorm1d(pred_dim), nn.ReLU(inplace=True),
            nn.Linear(pred_dim, proj_dim),
        )

    def forward(self, x: torch.Tensor):
        h = self.backbone(x)
        h = self.pool(h).flatten(1)
        z = self.projector(h)
        p = self.predictor(z)
        return p, z.detach()


def simsiam_loss(p1, z2, p2, z1) -> torch.Tensor:
    return -(F.cosine_similarity(p1, z2, dim=-1).mean()
             + F.cosine_similarity(p2, z1, dim=-1).mean()) / 2.0


def main() -> None:
    args = parse_args()
    if not args.data_root:
        sys.exit("ERROR: --data-root (or $VISCLICK_DATA) is required.")
    data_root = Path(args.data_root).resolve()
    if not data_root.is_dir():
        sys.exit(f"ERROR: data root does not exist: {data_root}")

    print(f"data_root  = {data_root}")
    print(f"epochs     = {args.epochs}")
    print(f"batch      = {args.batch}")
    print(f"img_size   = {args.img_size}")
    print(f"workers    = {args.workers}")
    print(f"max_corpus = {args.max_corpus or 'no cap'}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda":
        print(f"device     = cuda ({torch.cuda.get_device_name(0)})")
    else:
        print("device     = cpu  (training will be slow)")

    print("\n--- corpus ---")
    corpus = collect_corpus(data_root, args.max_corpus)
    print(f"REPORT corpus | size = {len(corpus)} | head = {corpus[:2]}")
    if len(corpus) < 1000:
        sys.exit(f"ERROR: corpus too small ({len(corpus)} < 1000). "
                 f"Check {data_root}/unified/<split>/images/ and "
                 f"{data_root}/source_train_bundles/<split>.tar.gz")

    loader = DataLoader(
        TwoViewDataset(corpus, simsiam_aug(args.img_size), args.img_size),
        batch_size=args.batch, shuffle=True, num_workers=args.workers,
        pin_memory=(device == "cuda"), drop_last=True,
        persistent_workers=(args.workers > 0),
    )
    print(f"REPORT loader | batch = {args.batch} | steps_per_epoch = {len(loader)}")

    print("\n--- backbone ---")
    source_wts = data_root / "weights" / "baseline_source" / "best_source_v8s.pt"
    if not source_wts.is_file():
        sys.exit(f"ERROR: source weights missing: {source_wts}")
    src = YOLO(str(source_wts))
    n_backbone = 10
    backbone_modules = list(src.model.model[:n_backbone])
    backbone = nn.Sequential(*backbone_modules).to(device).eval()
    with torch.no_grad():
        feat = backbone(torch.zeros(1, 3, args.img_size, args.img_size, device=device))
    feat_dim = feat.shape[1]
    print(f"REPORT backbone | modules = {len(backbone_modules)} "
          f"| feat = {tuple(feat.shape)} | channels = {feat_dim}")

    model = SimSiam(backbone, feat_dim=feat_dim).to(device)
    print(f"REPORT simsiam | params = {sum(p.numel() for p in model.parameters()):,}")

    ssp_dir = data_root / "weights" / "ssp"
    ssp_dir.mkdir(parents=True, exist_ok=True)
    ckpt_path = ssp_dir / "ssp_ckpt.pt"
    loss_csv = ssp_dir / "ssp_loss_log.csv"
    backbone_out = ssp_dir / "backbone_simsiam.pt"

    base_lr = 0.05 * args.batch / 256.0
    optimizer = torch.optim.SGD(model.parameters(), lr=base_lr, momentum=0.9, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    start_epoch = 0
    if args.force_fresh:
        for p in (ckpt_path, loss_csv):
            if p.is_file():
                p.unlink(); print(f"FORCE_FRESH: removed {p}")
    elif ckpt_path.is_file():
        ck = torch.load(ckpt_path, map_location=device)
        if ck.get("epochs_target") == args.epochs:
            model.load_state_dict(ck["model"])
            optimizer.load_state_dict(ck["optimizer"])
            scheduler.load_state_dict(ck["scheduler"])
            start_epoch = ck["epoch"]
            print(f"RESUME from epoch {start_epoch}/{args.epochs}")
        else:
            print(f"checkpoint targets EPOCHS={ck.get('epochs_target')} != {args.epochs}; "
                  f"ignoring (training fresh)")

    if start_epoch == 0:
        with open(loss_csv, "w", newline="") as fh:
            csv.writer(fh).writerow(["epoch", "avg_loss", "lr", "elapsed_s"])

    print(f"\n--- training {args.epochs - start_epoch} epoch(s) ---")
    for epoch in range(start_epoch, args.epochs):
        t0 = time.time()
        model.train()
        losses: list[float] = []
        for v1, v2 in loader:
            v1 = v1.to(device, non_blocking=True)
            v2 = v2.to(device, non_blocking=True)
            p1, z1 = model(v1)
            p2, z2 = model(v2)
            loss = simsiam_loss(p1, z2, p2, z1)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses.append(loss.item())
        scheduler.step()
        avg = sum(losses) / max(1, len(losses))
        dt = time.time() - t0
        lr = scheduler.get_last_lr()[0]
        print(f"epoch {epoch+1:02d}/{args.epochs} | loss = {avg:+.4f} | lr = {lr:.5f} | {dt:.1f}s")
        with open(loss_csv, "a", newline="") as fh:
            csv.writer(fh).writerow([epoch + 1, round(avg, 4), round(lr, 5), round(dt, 1)])
        torch.save({
            "epoch": epoch + 1,
            "epochs_target": args.epochs,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "scheduler": scheduler.state_dict(),
        }, ckpt_path)

    torch.save(model.backbone.state_dict(), backbone_out)
    size_mb = backbone_out.stat().st_size / 1024 / 1024
    print(f"\nREPORT backbone_out | path = {backbone_out} | size_mb = {size_mb:0.1f}")
    print("REPORT step = SSP_TRAIN | status = done")


if __name__ == "__main__":
    main()
