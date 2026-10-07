# Spec: Laya ticket-type classifier, compared with Logistic Regression

Status: ready-for-agent

Language: this spec uses ASD-STE100 Simplified Technical English. Sentences are short. Each instruction has one action. Verbs are in the active voice.

## Problem Statement

The ticket classifier project has a frozen baseline model. The baseline is TF-IDF with Logistic Regression (balanced). It predicts the ticket type: Incident, Request, Problem or Change.

On the test set, the baseline gets 79.95% accuracy and 0.815 macro F1. Problem recall is 60%. Most errors are Incident and Problem tickets that the model mixes up. Step 17 of the baseline notebook shows that a bag-of-words model is at its ceiling on this data. Tuning changed accuracy by −0.2 points.

The user wants to know if a stronger model type can do better on the same data. Laya is an open-weight decision model on Hugging Face (`convaiinnovations/laya`, ModernBERT-large, 421M parameters, English, Apache-2.0). Laya can work zero-shot. Laya can also be fine-tuned. The user does not know how Laya compares with the baseline on these tickets. The user also does not know if fine-tuning is possible on their Mac.

## Solution

Build a new project folder for Laya. Give Laya the same tickets, the same input text, the same target and the same split as the baseline.

Measure three models on the same rows:

1. Model A: the frozen baseline (Logistic Regression). Do not train it again.
2. Model B: Laya zero-shot. Ask Laya one typed "choice" question with the four ticket types.
3. Model C: Laya fine-tuned on the training rows only.

Do the fine-tuning on the user's Mac (Apple M3, 16 GB, MPS). If the Mac cannot complete the fine-tuning, move the training step to a cloud GPU (Colab). Keep all other steps the same.

Show the result as one notebook. The notebook ends with one comparison table and a clear decision. Laya replaces the baseline only if Laya gains more than 1 point of accuracy. The table also shows the cost of each model.

## User Stories

1. As a data scientist, I want Laya to read the same `subject` and `body` text as the baseline, so that the comparison is fair.
2. As a data scientist, I want Laya to use the exact train, validation and test rows of the baseline, so that a different split cannot change the result.
3. As a data scientist, I want a check that stops the notebook if the row sets are different, so that I cannot compare on different data by accident.
4. As a data scientist, I want the families of reworded tickets to stay on one side of every split, so that Laya cannot score by recognition.
5. As a data scientist, I want `type`, `answer`, `priority`, `queue` and `tags` to stay out of the input, so that no column that is added after handling can leak the label.
6. As a data scientist, I want the same text cleaning as the baseline, so that a cleaning difference cannot explain a score difference.
7. As a data scientist, I want a zero-shot Laya score on validation before any training, so that I know what fine-tuning adds.
8. As a data scientist, I want to write the four ticket types as one Laya "choice" question with clear criteria, so that the zero-shot model uses Laya as its authors intend.
9. As a data scientist, I want a smoke test on a small set of validation rows first, so that I find setup errors in minutes, not hours.
10. As a data scientist, I want to fine-tune Laya on the training rows only, so that validation and test stay clean.
11. As a data scientist, I want to select epochs, learning rate and other settings on validation only, so that the test set stays sealed until the end.
12. As a data scientist, I want to fine-tune on my Mac with MPS first, so that I do not need a cloud account for the first attempt.
13. As a data scientist, I want to record the training time, the peak memory and the device for each run, so that I can state the cost of fine-tuning.
14. As a data scientist, I want a clear stop rule for the Mac attempt, so that I know when to move to Colab.
15. As a data scientist, I want the Colab path to use the same data files and the same settings, so that a change of device does not change the experiment.
16. As a data scientist, I want to save the fine-tuned checkpoint outside git, so that large model files do not go into the repository.
17. As a data scientist, I want each model to write its predictions to one file per split in the same format, so that one scoring step can compare all models.
18. As a data scientist, I want one scoring function for all models, so that a metric difference cannot come from different code.
19. As a data scientist, I want accuracy, macro F1 and recall for each type, so that I can compare with the baseline model card.
20. As a data scientist, I want Incident and Problem recall shown side by side for each model, so that I can see if Laya fixes the main weak spot of the baseline.
21. As a data scientist, I want a calibration error (ECE) for each model, so that I know if the confidence of each model is honest.
22. As a data scientist, I want the share of tickets that each model can auto-route at the baseline threshold (confidence ≥ 0.75), so that I can compare the product value directly.
23. As a data scientist, I want each Laya model to find its own auto-route threshold on validation with the same 95% accuracy target, so that the comparison does not punish a model with a different confidence scale.
24. As a data scientist, I want family-level bootstrap 95% ranges on the test metrics, so that I can see if a difference is larger than the noise.
25. As a data scientist, I want the test set opened once for each Laya model, after all selection is complete, so that the test result is honest.
26. As a data scientist, I want the baseline test numbers read from its model card, not computed again, so that the frozen result does not change.
27. As a data scientist, I want the latency for each ticket and the model size for each model, so that I can compare the cost of a deployment.
28. As a data scientist, I want the decision rule written before training, so that I cannot move the rule after I see the result.
29. As a data scientist, I want an error analysis of the Laya mistakes on validation, so that I can see if Laya makes the same mistakes as the baseline.
30. As a data scientist, I want to see tickets where Laya and the baseline disagree, so that I can understand where each model is stronger.
31. As a data scientist, I want a model card for the fine-tuned Laya in the same format as the baseline card, so that the two cards are easy to compare.
32. As a data scientist, I want the project to have its own virtual environment on Python 3.12, so that torch and Laya install correctly and the other projects do not change.
33. As a data scientist, I want pinned versions in a requirements file, so that I can run the notebook again and get the same result.
34. As a data scientist, I want a fixed seed for every random step, so that each run gives the same numbers.
35. As a reader of the portfolio site, I want the notebook to render without code, like the ticket classifier page, so that I can read the story without Python knowledge.
36. As a reader of the portfolio site, I want the notebook to explain each phase in plain language, so that I can follow why each decision was made.
37. As a reader of the portfolio site, I want one final table and one sentence that states the winner, so that I know the result quickly.
38. As a hiring manager, I want to see that the author kept the test set sealed and wrote the rules first, so that I can trust the method.

## Implementation Decisions

### Modules

- **New project folder `laya-discover`.** It holds one notebook, its own virtual environment and its own requirements file. This matches the other project folders.
- **Split export in the baseline notebook.** Add one small step to the baseline notebook. The step writes the row ids, the family id and the split name (train, validation, test) for each English ticket to a small data file. The step does not change any model or any result in the baseline.
- **Laya notebook.** It reads the raw data, applies the same cleaning, and joins on the exported split file. It does not compute a new split.
- **Prediction files.** Each model writes one predictions file for each split. Each row has: row id, split, true type, predicted type, confidence, and one probability for each of the four types.
- **One scoring step.** It reads the prediction files. It computes all metrics with the same code for all models.

### Data and input

- Input text is `subject` + `body` after the baseline cleaning. Cleaning removes `\n` and `<br>` leftovers. It replaces emails, URLs and long numbers with placeholders.
- English tickets only. This is the same population as the baseline (16,338 tickets).
- The target is `type` with four values: Incident, Request, Problem, Change.
- Laya `convaiinnovations/laya` has a 512-token limit. Count the tickets that are longer than this limit. Report the count. Cut the long tickets at the limit.

### Laya models

- Model B uses the `laya` package. It sends each ticket as the state. It asks one "choice" question with the four types and one short criterion for each type. Write the criteria from the type meanings, not from the test data.
- Model C uses the official Laya fine-tune script for Apple Silicon as the starting point. Change the dataset step only, so that it reads our training rows.
- Fine-tuning selects its settings on validation. Use the same tie rule as the baseline: accuracy decides. Results within 1 point are a tie. A tie goes to the higher macro F1.
- Stop rule for the Mac: move to Colab if one epoch takes more than 3 hours, or if the run fails with an out-of-memory error after the batch size is reduced to its minimum.
- Save checkpoints in the project folder in a path that git ignores.

### Comparison and decision

- The baseline numbers come from its model card. They are frozen.
- Laya replaces the baseline only if Laya test accuracy is more than 1 point higher. The final table states the cost next to the gain.
- Report for each model: accuracy, macro F1, recall for each type, ECE, auto-route share and accuracy at threshold 0.75, the model's own threshold for 95% accuracy, latency for each ticket on the Mac, and model size.

### Environment

- Python 3.12 (it is installed through Homebrew). The system default Python is 3.14. Torch and Laya support for 3.14 is not certain.
- Pin `laya`, `torch`, `transformers`, `pandas`, `scikit-learn` and `numpy` versions after the first good install.

### Site

- Publish the notebook as a new page later, with the same render step as the ticket classifier page. This is a separate change to the deploy workflow.

## Testing Decisions

- **A good test checks external behavior only.** It checks what goes in and what comes out. It does not check the internal steps.
- **Seam 1 (the main seam): the split file.** An assert stops the Laya notebook if its train, validation and test row ids are not equal to the baseline row ids. Another assert stops the notebook if one family is in two splits.
- **Seam 2: the prediction file contract.** An assert checks each prediction file before scoring. It checks the column names, the four type names, that the probabilities add up to 1, and that the row ids are equal to the split rows.
- **Scoring check.** Score the baseline predictions on validation with the new scoring step. The result must be equal to the baseline notebook values. This proves that the scoring step is correct.
- **Smoke test.** Run Model B on 50 validation rows before the full run. The run must complete and write a valid prediction file.
- **Prior art.** The baseline notebook already uses `assert` statements for the family split and for missing columns. Use the same style. Do not add a test framework.

## Out of Scope

- German tickets and the `laya-multilingual` checkpoint.
- Department (`queue`) as a target. The baseline showed that the department labels are not reliable.
- Any change to the baseline model, its split or its reported results.
- Other large models (for example sentence-embedding models or LLMs). Laya is the only new model in this spec.
- Deployment of Laya as a service (`laya[serve]`, ONNX export, MCP).
- The change to the deploy workflow that adds a Laya page to the site.
- Real (not synthetic) tickets.

## Further Notes

- The baseline test set was already opened once. Laya does not change this. Laya selects all settings on validation and sees the test set once. The comparison on test is fair because neither model used test for selection.
- The dataset is synthetic. The result shows how the two methods compare on this data. It does not show performance on a real inbox.
- The Laya model card says that the base model scored 0.362 zero-shot and 0.766 after fine-tuning on its own benchmark. Expect a large gap between Model B and Model C here too. Do not assume this gap before you measure it.
- Open question: the baseline confuses Incident and Problem because the labels themselves are not consistent. If Laya also stays near 80%, the label noise is the ceiling, not the model.
