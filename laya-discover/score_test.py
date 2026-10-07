"""Open the sealed test set ONCE: Model A, Model B, Model D seeds 42 and 43 (chosen epochs, raw and calibrated).

Refuses to run if any predictions/*_test.csv exists - that file is the seal. Writes all files at the end.
Run from laya-discover/:  .venv/bin/python score_test.py > logs/score_test.log 2>&1
"""
import json
import sys
from pathlib import Path

import joblib
import laya
import numpy as np
import pandas as pd
import torch
from laya.calibrate import records_from_labeled
from sklearn.metrics import accuracy_score, f1_score, log_loss, recall_score
from sklearn.model_selection import GroupKFold

import train_arm_d as d

TYPES, Q, PRED = np.array(d.TYPES), d.TYPE_QUESTION, d.PRED_DIR
CHOSEN = {42: 3, 43: 2}  # chosen on validation by the pre-registered rule (seed 43: epoch 2, macro F1 tie-break)
P_COLS = [f"p_{t}" for t in TYPES]

if list(PRED.glob("*_test.csv")):
    sys.exit("Test set already opened (predictions/*_test.csv exists). Refusing to look again.")

t = d.load_tickets().join(pd.read_csv(d.SPLITS_FILE)["text_clean"])
val, test = (t[t["split"] == s].reset_index(drop=True) for s in ("validation", "test"))
assert len(val) == len(test) == 2334


def softmax_t(z, T):
    z = z / T - (z / T).max(1, keepdims=True)
    return np.exp(z) / np.exp(z).sum(1, keepdims=True)


def fit_temperature(z, y):  # same as the notebook: minimise log-loss over log T, clamp [0.5, 5]
    zt, yt = torch.tensor(z, dtype=torch.float64), torch.tensor(y)
    log_t = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    opt = torch.optim.LBFGS([log_t], lr=0.1, max_iter=500)

    def closure():
        opt.zero_grad()
        loss = torch.nn.functional.cross_entropy(zt / log_t.exp(), yt)
        loss.backward()
        return loss
    opt.step(closure)
    return float(log_t.exp().clamp(0.5, 5.0))


def ece(conf, correct, bins=10):
    b = np.minimum((conf * bins).astype(int), bins - 1)
    return sum(abs(correct[b == i].mean() - conf[b == i].mean()) * (b == i).mean() for i in range(bins) if (b == i).any())


def logits_of(agent, rows):  # raw logits via Laya's own function (probabilities are rounded to 4 decimals)
    pairs = [(s, Q, {"ticket_type": [1.0 if x == y else 0.0 for x in TYPES]}) for s, y in zip(rows["text_raw"], rows["type"])]
    L = np.stack([r[1] for r in records_from_labeled(agent, pairs)])
    assert L.shape == (len(rows), 4)
    return L


def pred_frame(rows, proba):
    p = pd.DataFrame({"raw_row": rows["raw_row"], "split": "test", "type": rows["type"],
                      "pred": TYPES[proba.argmax(1)], "conf": proba.max(1)})
    p[P_COLS] = proba
    return p


out = {}  # file stem -> prediction frame

# Model A - frozen baseline, cleaned text
lr = joblib.load(d.BASELINE_DIR / "artifacts" / "type_classifier.joblib")
out["arm_a_lr"] = pred_frame(test, pd.DataFrame(lr.predict_proba(test["text_clean"]), columns=lr.classes_)[list(TYPES)].to_numpy())

# Model B - zero-shot, raw text, base weights
agent = laya.load(d.MODEL_ID)
res = agent.predict_batch(test["text_raw"].tolist(), Q, batch_size=32, sort_by_length=True)
out["arm_b_zeroshot_raw"] = pred_frame(test, np.array([[r["answers"]["ticket_type"]["probabilities"][x] for x in TYPES] for r in res]))
del agent

# Model D - per seed: validation logits -> temperature (keep rule, out of fold) -> test logits
y_val = val["type"].map({x: i for i, x in enumerate(TYPES)}).to_numpy()
for seed, ep in CHOSEN.items():
    agent = laya.load(str(d.CHECKPOINTS / f"seed{seed}" / f"epoch{ep}"))
    npy = PRED / f"arm_d_seed{seed}_epoch{ep}_validation_logits.npy"
    if npy.exists():
        Lv = np.load(npy)
    else:
        Lv = logits_of(agent, val)
        np.save(npy, Lv)
    oof = np.zeros_like(Lv)
    for tr, te in GroupKFold(5).split(Lv, y_val, val["family_id"]):
        oof[te] = softmax_t(Lv[te], fit_temperature(Lv[tr], y_val[tr]))
    raw = softmax_t(Lv, 1.0)
    ece_raw = ece(raw.max(1), raw.argmax(1) == y_val)
    ece_oof = ece(oof.max(1), oof.argmax(1) == y_val)
    keep = ece_oof < ece_raw and log_loss(y_val, oof, labels=range(4)) <= log_loss(y_val, raw, labels=range(4))
    T = fit_temperature(Lv, y_val) if keep else 1.0
    print(f"seed {seed} epoch {ep}: validation ECE raw {ece_raw:.3f} -> out-of-fold {ece_oof:.3f} · keep {keep} · T = {T:.3f}")
    Lt = logits_of(agent, test)
    np.save(PRED / f"arm_d_seed{seed}_epoch{ep}_test_logits.npy", Lt)
    out[f"arm_d_seed{seed}_epoch{ep}_raw"] = pred_frame(test, softmax_t(Lt, 1.0))
    out[f"arm_d_seed{seed}_calibrated"] = pred_frame(test, softmax_t(Lt, T))
    del agent

# Score first, then write the seal files
rows = []
for name, p in out.items():
    y, pr, c = p["type"].to_numpy(), p["pred"].to_numpy(), p["conf"].to_numpy()
    rows.append({"arm": name, "accuracy": accuracy_score(y, pr), "macro F1": f1_score(y, pr, labels=TYPES, average="macro"),
                 "recall Problem": recall_score(y, pr, labels=["Problem"], average=None)[0],
                 "ECE": ece(c, y == pr), "auto-routed @0.75": (c >= 0.75).mean(),
                 "accuracy @0.75": (y == pr)[c >= 0.75].mean()})
print(pd.DataFrame(rows).set_index("arm").round(4).to_string())
for name, p in out.items():
    p.to_csv(PRED / f"{name}_test.csv", index=False)
print("written:", ", ".join(f"{n}_test.csv" for n in out))
