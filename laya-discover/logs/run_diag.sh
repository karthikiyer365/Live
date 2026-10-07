#!/bin/bash
# Three diagnostic runs, full configuration with warmup, each stopped at 2,400 tickets.
cd "$(dirname "$0")/.."
for v in "no_checkpointing:--no-checkpointing" "lr_scale_0.3:--lr-scale 0.3" "no_rl:--no-rl"; do
  name=${v%%:*}; flags=${v#*:}
  caffeinate -i .venv/bin/python train_arm_d.py --seed 42 --max-tickets 2400 $flags > logs/diag_$name.log 2>&1
  echo "== $name (exit $?)"; grep -E "^\[|ABORT|Error" logs/diag_$name.log | cut -c1-200
done
