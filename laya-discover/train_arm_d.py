"""Arm D: fine-tune Laya on the ticket-type training rows (Apple Silicon / MPS).

Vendored from Laya's official Apple-Silicon fine-tune script (Apache-2.0):
  https://github.com/NandhaKishorM/laya/blob/main/notebooks/laya_finetune_typed_decisions_mps.py
  read 2026-10-05. The training step (loss, optimizer, schedule, clipping) is unchanged.

Changes from the official script, each required by the evaluation rules in
.scratch/laya-discover/spec.md:
  1. Data   — our 11,670 training rows from splits.csv, raw subject + body, Arm B's exact
              question, one-hot targets. Validation and test rows never enter training.
  2. Seed   — --seed drives the data order and the RL noise (the original hard-codes 42 + epoch
              for the order and never seeds the noise).
  3. Epochs — every epoch is saved to its own folder (the original overwrites one folder), then
              reloaded with laya.load and scored on validation through the same prediction-file
              format as Arms A-C. Epoch checkpoints carry temperature 1.0, so scores are raw.
  4. Calibration — removed here. The original fits temperatures on a random 10% of training rows,
              which holds reworded siblings of training tickets. The notebook fits the temperature
              on validation instead, after the epoch is chosen.
  5. Warmup — linear learning-rate warmup over the first 10% of updates, then the same cosine decay.
              Without it, seed 42 diverged in the first ~12 updates.
  6. Loss   — cross-entropy only; Laya's RL term is off by default (--rl adds it back). With it, training
              diverged by ~1,400-1,800 tickets even with warmup or a 0.3x learning rate; without it,
              cross-entropy kept falling past 2,400 (logs/diag_*.log). Cross-entropy is itself a proper
              scoring rule, and calibration is still checked on validation.
  7. Abort  — stops on a NaN/inf loss, or when the 100-step mean loss doubles from the first 100 steps.

Usage (from laya-discover/; picks cuda > mps > cpu, training stays fp32 on every device):
  caffeinate -i .venv/bin/python train_arm_d.py --seed 42 > logs/arm_d_seed42.log 2>&1
  .venv/bin/python train_arm_d.py --seed 42 --epochs 1 --limit 200 --val-limit 100 --tag smoke
"""

import argparse
import gc
import json
import math
import random
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from huggingface_hub import snapshot_download
from safetensors.torch import load_file, save_file
from transformers import AutoTokenizer

import laya
from laya.agent import _fix_tokenizer_config
from laya.common import QTYPES, build_model, build_sequence, proper_reward, render_options

MODEL_ID = "convaiinnovations/laya"
HERE = Path(__file__).resolve().parent
BASELINE_DIR = HERE.parent / "topic-classification"
RAW_FILE = BASELINE_DIR / "data" / "aa_dataset-tickets-multi-lang-5-2-50-version.csv"
SPLITS_FILE = BASELINE_DIR / "artifacts" / "splits.csv"
CHECKPOINTS = HERE / "checkpoints"
PRED_DIR = HERE / "predictions"

TYPES = ["Incident", "Request", "Problem", "Change"]
# Identical to Arm B's question in laya_classifier.ipynb (Phase 5 asserts this). It is part of the model input.
TYPE_QUESTION = {"ticket_type": {"type": "choice",
    "instructions": "What type of IT support ticket is this?",
    "criteria": {
        "Incident": "something is broken, down or not working right now and needs a fix",
        "Request":  "asks for information, access, help or a standard service; nothing is broken",
        "Problem":  "a recurring or underlying cause behind repeated failures that needs investigation",
        "Change":   "asks to add, upgrade, modify or improve a system, feature or configuration"}}}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def load_tickets():
    """The baseline's split plus raw text, joined exactly as laya_classifier.ipynb Step 2 does it."""
    splits = pd.read_csv(SPLITS_FILE)
    raw = pd.read_csv(RAW_FILE, usecols=["subject", "body", "type"])
    t = splits.join(raw, on="raw_row", rsuffix="_raw")
    assert (t["type"] == t["type_raw"]).all(), "splits.csv does not line up with the raw CSV"
    t["text_raw"] = (t["subject"].fillna("") + " " + t["body"].fillna("")).str.strip()
    return t[["raw_row", "family_id", "split", "type", "text_raw"]]


def build_training_item(tokenizer, cfg, state, true_type):
    question = TYPE_QUESTION["ticket_type"]
    criteria = question["criteria"]
    target = [1.0 if k == true_type else 0.0 for k in criteria]   # one-hot (decision Q3)
    sequence, markers = build_sequence(
        tokenizer, state, {"t": "choice", "ins": question["instructions"], "crit": criteria},
        cfg["max_len"], cfg["head_max_len"],
    )
    assert len(markers) == len(render_options({"t": "choice", "crit": criteria})) == 4
    return {"ids": sequence, "markers": markers, "qtype": QTYPES["choice"], "target": target}


def collate(items, pad_id):  # unchanged from the official script
    batch_size = len(items)
    seq_len = max(len(item["ids"]) for item in items)
    kmax = max(len(item["markers"]) for item in items)
    input_ids = torch.full((batch_size, seq_len), pad_id, dtype=torch.long)
    attention = torch.zeros((batch_size, seq_len), dtype=torch.long)
    marker_pos = torch.zeros((batch_size, kmax), dtype=torch.long)
    marker_mask = torch.zeros((batch_size, kmax), dtype=torch.bool)
    target = torch.zeros((batch_size, kmax), dtype=torch.float32)
    for i, item in enumerate(items):
        length = len(item["ids"])
        input_ids[i, :length] = torch.tensor(item["ids"], dtype=torch.long)
        attention[i, :length] = 1
        k = len(item["markers"])
        marker_pos[i, :k] = torch.tensor(item["markers"], dtype=torch.long)
        marker_mask[i, :k] = True
        target[i, :len(item["target"])] = torch.tensor(item["target"], dtype=torch.float32)
    return (input_ids, attention, marker_pos, marker_mask, target,
            torch.tensor([item["qtype"] for item in items], dtype=torch.long))


def save_checkpoint(model, tokenizer, cfg, path, meta):
    """fp16 weights + configs, loadable with laya.load(path). Temperatures reset to 1.0 = raw scores."""
    path.mkdir(parents=True, exist_ok=True)
    weights = {n: v.detach().half().cpu().contiguous() for n, v in model.state_dict().items()}
    save_file(weights, str(path / "model.safetensors"))
    model.encoder.config.save_pretrained(path / "encoder")
    tokenizer.save_pretrained(path / "tokenizer")
    out_cfg = {**cfg, "fine_tuned": True, "model_name": "laya-arm-d", "temperature": [1.0, 1.0, 1.0]}
    out_cfg.pop("temperature_by_options", None)
    out_cfg.pop("gradient_checkpointing", None)
    (path / "rl_agent_config.json").write_text(json.dumps(out_cfg, indent=2))
    (path / "checkpoint_meta.json").write_text(json.dumps(meta, indent=2))


def score_validation(ckpt_dir, val, tag):
    """Reload the saved epoch the way it would be served, write a prediction file in the shared format."""
    agent = laya.load(str(ckpt_dir))
    t0 = time.perf_counter()
    out = agent.predict_batch(val["text_raw"].tolist(), TYPE_QUESTION, batch_size=32, sort_by_length=True)
    seconds = time.perf_counter() - t0
    proba = np.array([[r["answers"]["ticket_type"]["probabilities"][t] for t in TYPES] for r in out])
    pred = pd.DataFrame({"raw_row": val["raw_row"].to_numpy(), "split": "validation", "type": val["type"].to_numpy(),
                         "pred": np.array(TYPES)[proba.argmax(1)], "conf": proba.max(1)})
    pred[[f"p_{t}" for t in TYPES]] = proba
    PRED_DIR.mkdir(exist_ok=True)
    pred.to_csv(PRED_DIR / f"{tag}_validation.csv", index=False)
    del agent
    gc.collect()
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return (pred["pred"] == pred["type"]).mean(), seconds / len(val)


def train(args):
    torch.manual_seed(args.seed)
    if args.device == "auto":
        args.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
    device = torch.device(args.device)
    torch.cuda.manual_seed_all(args.seed)  # no-op without CUDA
    model_dir = Path(snapshot_download(MODEL_ID, allow_patterns=["*.json", "*.safetensors", "encoder/*", "tokenizer/*"],
                                       ignore_patterns=["multilingual/*", "typed-decisions/*", "eval/*"]))
    _fix_tokenizer_config(str(model_dir))
    cfg = json.loads((model_dir / "rl_agent_config.json").read_text())
    cfg.update({"max_tokens_per_batch": 2048, "max_len": 1024, "head_max_len": 256})   # as the official script
    if not args.no_checkpointing:
        cfg["gradient_checkpointing"] = True

    tokenizer = AutoTokenizer.from_pretrained(model_dir / "tokenizer")
    model = build_model(cfg, encoder_dir=model_dir / "encoder")
    model.load_state_dict(load_file(str(model_dir / "model.safetensors")), strict=True)
    model.float()
    if not args.no_checkpointing:
        model.encoder.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.head_checkpointing = True
    model.to(device).train()

    tickets = load_tickets()
    train_rows = tickets[tickets["split"] == "train"]
    val = tickets[tickets["split"] == "validation"].reset_index(drop=True)
    if args.limit:
        train_rows = train_rows.sample(args.limit, random_state=args.seed)
    if args.val_limit:
        val = val.head(args.val_limit)
    assert not set(train_rows["family_id"]) & set(tickets.loc[tickets["split"] != "train", "family_id"])
    train_items = [build_training_item(tokenizer, cfg, s, y) for s, y in zip(train_rows["text_raw"], train_rows["type"])]

    encoder_params = [p for n, p in model.named_parameters() if "encoder." in n]
    head_params = [p for n, p in model.named_parameters() if "encoder." not in n]
    optimizer = torch.optim.AdamW(
        [{"params": encoder_params, "lr": 2.5e-5 * args.lr_scale}, {"params": head_params, "lr": 1e-4 * args.lr_scale}],
        weight_decay=0.01)
    updates = max(1, math.ceil(len(train_items) / args.micro_batch / args.grad_accum) * args.epochs)
    # Linear warmup, then the official cosine decay. Added after seed 42 diverged at full learning rate:
    # cross-entropy rose 0.96 -> 2.51 within the first ~12 updates (logs/arm_d_seed42_check.log).
    warmup = max(1, round(args.warmup_frac * updates))
    scheduler = torch.optim.lr_scheduler.SequentialLR(optimizer, [
        torch.optim.lr_scheduler.LinearLR(optimizer, start_factor=0.01, total_iters=warmup),
        torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=updates - warmup, eta_min=1e-6),
    ], milestones=[warmup])

    run_dir = CHECKPOINTS / f"{args.tag}seed{args.seed}"
    log(f"device={device} seed={args.seed} train={len(train_items):,} val={len(val):,} "
        f"micro_batch={args.micro_batch} grad_accum={args.grad_accum} epochs={args.epochs} updates={updates:,} warmup={warmup} "
        f"lr_scale={args.lr_scale} rl={args.rl} checkpointing={not args.no_checkpointing} abort={not args.no_abort}")

    first_window, window = None, []
    for epoch in range(args.epochs):
        random.Random(args.seed + epoch).shuffle(train_items)
        optimizer.zero_grad(set_to_none=True)
        total_loss, n_batches, n_updates = 0.0, 0, 0
        ce_sum, rl_sum = 0.0, 0.0  # since the last progress line
        sigma = 0.4 + (0.1 - 0.4) * epoch / max(1, args.epochs - 1)
        t_epoch = time.perf_counter()

        for start in range(0, len(train_items), args.micro_batch):
            chunk = train_items[start:start + args.micro_batch]
            ids, attention, positions, mask, target, qtype = (x.to(device) for x in collate(chunk, tokenizer.pad_token_id))

            # ── training step: the official script, lines 294–328; only the RL term's inclusion is switchable ──
            logits, activation = model(ids, attention, positions, mask, qtype)
            logits = logits.float()
            k = mask.sum(-1, keepdim=True).float()
            eps = torch.randn((4,) + logits.shape, device=device) * sigma * mask
            eps = (eps - eps.sum(-1, keepdim=True) / k) * mask
            noisy_logits = logits.detach().unsqueeze(0) + eps
            probabilities = torch.softmax(noisy_logits.masked_fill(~mask, -1e4), -1)
            with torch.no_grad():
                reward = proper_reward(probabilities, target.unsqueeze(0), qtype, mask, w_sph=0.75, w_rps=1.0)
                advantage = reward - reward.mean(0, keepdim=True)
                advantage = advantage / (advantage.std() + 1e-6)
            logp = -(((noisy_logits - logits.unsqueeze(0)) ** 2) * mask).sum(-1) / (2 * sigma**2)
            loss_rl = -(advantage * logp).mean()
            loss_ce = -(target * torch.log_softmax(logits.masked_fill(~mask, -1e4), -1)).sum(-1).mean()
            loss = ((loss_rl if args.rl else 0.0) + loss_ce + 0.0 * activation.sum()) / args.grad_accum
            loss.backward()

            n_batches += 1
            if n_batches % args.grad_accum == 0 or start + args.micro_batch >= len(train_items):
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)
                n_updates += 1
            # ── end of unchanged step ──

            step_loss = loss.item() * args.grad_accum
            if not math.isfinite(step_loss):
                raise SystemExit(f"ABORT: loss is {step_loss} at epoch {epoch + 1}, micro-batch {n_batches}")
            total_loss += step_loss
            ce_sum, rl_sum = ce_sum + loss_ce.item(), rl_sum + loss_rl.item()
            window.append(step_loss)
            if len(window) == 100:
                mean = sum(window) / 100
                first_window = first_window or mean
                if mean > 2 * first_window and not args.no_abort:
                    raise SystemExit(f"ABORT: 100-step mean loss {mean:.3f} is more than 2x the first ({first_window:.3f}) · "
                                     f"this window: ce {ce_sum / 100:.3f}, rl {rl_sum / 100:+.3f}")
                window = []
            if n_batches % 100 == 0:
                done = start + len(chunk)
                eta_h = (time.perf_counter() - t_epoch) / done * (len(train_items) - done) / 3600
                mem = (torch.mps.driver_allocated_memory() if device.type == "mps" else
                       torch.cuda.max_memory_allocated() if device.type == "cuda" else 0) / 1e9
                log(f"epoch {epoch + 1}/{args.epochs} · {done:,}/{len(train_items):,} tickets · "
                    f"loss {total_loss / n_batches:.4f} (last 100: ce {ce_sum / 100:.3f}, rl {rl_sum / 100:+.3f}) · {device.type} {mem:.1f} GB · epoch ETA {eta_h:.2f} h")
                ce_sum, rl_sum = 0.0, 0.0

            if args.max_tickets and start + len(chunk) >= args.max_tickets:
                log(f"STOP at --max-tickets {args.max_tickets}; nothing saved")
                return

        epoch_h = (time.perf_counter() - t_epoch) / 3600
        ckpt = run_dir / f"epoch{epoch + 1}"
        save_checkpoint(model, tokenizer, cfg, ckpt, {"epoch": epoch + 1, "seed": args.seed, "train_hours": round(epoch_h, 3),
                                                      "avg_loss": total_loss / max(1, n_batches), "updates": n_updates})
        model.eval()
        acc, sec = score_validation(ckpt, val, f"arm_d_{args.tag}seed{args.seed}_epoch{epoch + 1}")
        model.train()
        log(f"EPOCH {epoch + 1} done · {epoch_h:.2f} h · {n_updates} updates · avg loss {total_loss / max(1, n_batches):.4f} · "
            f"validation accuracy {acc:.4f} ({sec:.3f} s/ticket) · saved {ckpt.relative_to(HERE)}")

    log("DONE")


def main():
    p = argparse.ArgumentParser(description="Arm D: fine-tune Laya on the ticket-type training rows")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=4)
    p.add_argument("--micro-batch", type=int, default=2)
    p.add_argument("--grad-accum", type=int, default=16)
    p.add_argument("--limit", type=int, default=0, help="train on a random subset (smoke test)")
    p.add_argument("--val-limit", type=int, default=0, help="score only the first N validation tickets (smoke test)")
    p.add_argument("--tag", default="", help="prefix for checkpoint/prediction names, e.g. 'smoke_'")
    p.add_argument("--device", choices=["auto", "cuda", "mps", "cpu"], default="auto")
    p.add_argument("--no-checkpointing", action="store_true")
    p.add_argument("--lr-scale", type=float, default=1.0, help="multiply both learning rates")
    p.add_argument("--rl", action="store_true", help="add back Laya's RL term (diverged on our data; off by default)")
    p.add_argument("--no-abort", action="store_true", help="keep the NaN check, skip the 2x-loss abort")
    p.add_argument("--max-tickets", type=int, default=0, help="stop after N training tickets, save nothing (diagnostics)")
    p.add_argument("--warmup-frac", type=float, default=0.1, help="share of updates with a linear learning-rate warmup")
    args = p.parse_args()
    if args.tag and not args.tag.endswith("_"):
        args.tag += "_"
    torch.set_float32_matmul_precision("high")
    train(args)


if __name__ == "__main__":
    main()
