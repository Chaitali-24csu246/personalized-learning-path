# Version 3 — adaptive practice update

This is an update for the supplied account-enabled Version 2 project, not a replacement course or a new database. The ZIP contains only new/changed files, preserving their repository paths. `PATCH_MANIFEST.json` lists their hashes and the original V2 hashes where applicable.

## Apply it

1. Export your student progress and keep a Git backup of the current working project.
2. Extract `learning-path-v3-update.zip` outside the repository.
3. From the existing repository, create a branch and merge the patch contents into it. On a Mac, this avoids Finder replacing whole folders:

```sh
git switch -c v3
rsync -av ~/Downloads/learning-path-v3-update/ ./
python3 -m pip install -r training/requirements.txt
python3 -m unittest discover -s tests -v
npm run check
npm test
python3 start.py --port 8001
```

Adjust the extracted folder path if necessary. If `v3` already exists, switch to that branch instead of creating it again. If you have edited these same files since the supplied V2 ZIP, review/merge those changes rather than overwriting them blindly. No files are deleted by this patch.

The website itself requires no NumPy installation; NumPy is for offline training, evaluation and development tests. Use Python 3.11+ for the pinned training dependency (CI uses 3.12) and Node 20+ for tests. The trained model is already included; do not retrain merely to run the site.

Your existing `web/config.js`, Supabase project, accounts and schema stay in place. Do not rerun schema.sql or provision existing accounts. V2 progress is extended in memory when loaded and saved on the next activity; old estimates/history are retained rather than replayed or reset. All subsequent scored answers use V3 evidence rules.

Review `git diff` and commit the paths listed in the manifest. Suggested commit title:

> feat: unify learner evidence and add adaptive DQN learning paths

Push the `v3` branch and open a PR into your working release branch. Existing CI triggers on main/PRs targeting main and can also be run manually; pushing v3 alone does not automatically deploy.

## Deploy the update to your existing Hugging Face Space

Upload these FOUR frontend files together, keeping your existing folder layout:

- `web/app.mjs`
- `web/engine.mjs`
- `web/policy.json`
- `web/styles.css`

If your Space has the contents of web/ at its root, upload the four files at that root. Keep the Space's README/YAML, content.json, config.js, videos, worker and other modules. The source tests/training files belong in GitHub; they do not run on the static host. Refresh the hosted page after upload and check sign-in, an MCQ, a coding submission and saving. This update does not add automatic GitHub-to-Hugging Face synchronization.

## What students will notice

- One starting-check entry, removed after a completed/partially finished check.
- Two reserved concept checks per topic: medium first, then hard after success or easy after an incorrect answer. Up to three targeted coding checks follow, one per syllabus stage. Finish for now saves a partial summary; each answer already saves its evidence. Navigation retains completed answers but does not resume an unfinished diagnostic sequence.
- Coding checks use existing exercises, not a newly created coding assessment bank. Other topics' coding remains explicitly unassessed until practised.
- Topic and general practice both use the trained scorer. Adaptive difficulty is the default; a manual Easy/Medium/Hard choice restricts the model to that within-topic level.
- All scored answers anywhere—starting check, checkpoint, general practice, topic practice and coding submission—feed the same topic records. Merely running code or reading a lesson is not scored evidence.
- The map shows recent attempts, the current recommendation and three provisional recommendations. Forecasts simulate 75% independent success on a copied profile; they are not fixed promises or changes to the actual progress record.
- Separate MCQ and coding estimates, recent sources/time and strengths/gaps are visible. Comfortable concepts can satisfy readiness without clicking lesson completion. Comfortable MCQs do not certify coding ability.
- No changed course prose, examples, question wording, video links, database schema or authentication code.

## Where RL actually acts

The old coarse Q-table has been replaced by a compact candidate-scoring Double DQN: 28 input features, 32 ReLU hidden units and one Q value per candidate. It evaluates topic/activity/difficulty choices using observable learner estimates, skill gaps, evidence counts, recent result/time, review gap, lesson exposure, repeated-question status, relative progress and a session-load proxy. It was trained offline for 8,000 synthetic episodes of 30 steps with replay and a target network; gamma is 0.90.

The load proxy rises after demanding/failed practice and falls after easier practice or a lesson. It is not a measurement of fatigue. The model can learn easier consolidation steps without a fixed “every third question must be easy” schedule. Item availability and prerequisites are deterministic constraints; exact item selection and mastery updates are not RL. Tie-breaking no longer favours syllabus order.

Reward uses simulated hidden knowledge change with forgetting, a step cost, and smaller explicit challenge/load/repetition terms. Hidden knowledge is never an input to the policy. Learning remains frozen after deployment: real attempts update learner state, not network weights. New/admin-edited topics use a labelled fallback until model validation. A neural network does not prove educational usefulness.

`training/behaviour_checks.json` records example outcomes for controlled profiles. Tests verify opposite MCQ/coding gaps produce different choices, a weak late topic can outrank strong earlier topics, changing network weights changes decisions, and the policy changes difficulty with proficiency and session load. This is evidence of operational adaptation, not a claim that rules could never achieve similar behaviour.

## Evidence rules and limits

Fresh independent MCQ evidence moves toward difficulty ceilings 0.50/0.80/1.00, with rate 0.38. Coding uses the passed-test fraction with rate 0.48. First independent diagnostic MCQs receive weight 1.5 so two independent medium/hard successes can establish provisional conceptual readiness. These are transparent heuristics, not calibrated psychometric measurements. A correct easy answer never lowers an already stronger estimate.

Fresh independent question families receive full weight. Corrected short-gap retries receive weight 0.3; spaced repeats after eight learning steps receive weight 0.2; same-result immediate repeats and assisted attempts add no mastery credit. Every scored attempt is still logged, and repeated failures affect the failure indicator. Prior V2 credited families receive reduced evidence weight on their first V3 repeat. Recently attempted families are excluded from next-question selection until spaced; if a focused pool is exhausted, the app offers broader practice rather than claiming unlimited new questions.

Active seconds exclude hidden-tab time, idle periods beyond 60 seconds, and worker execution/loading. Time is logged and included as supporting policy input; it does not directly turn speed into mastery. Coding drafts remain saved. All assistance controls from V2 remain in force.

The existing finite bank remains 240 MCQs (180 practice, 60 reserved) and 60 coding tasks. Reserved tracing questions share families with related practice variants; credit is shared across that family. No claim is made that all questions in a nominal level have been empirically calibrated to equal difficulty.

## Validation and reproduction

- All 59 local tests pass: 14 Python and 45 JavaScript engine/controller/cloud tests. Controller tests use DOM/worker stubs; browser checks additionally exercised the real pages with mocked Supabase.
- Browser checks covered map, partial and full 43-item diagnostic (including three real coding checks), topic MCQ, shared saved progress, coding-draft saving and mobile overflow. Real Python execution was also checked in Chromium with the existing worker and locally served copies of pinned Pyodide 0.27.7 assets. Live Supabase, the hosted deployment and external CDN delivery were not verified; the hosted coding/assessment flow still needs your smoke check.
- Held-out simulation: 100 learners per method in two settings; RL, rules, fixed, random, training-only neighbour collaborative filtering and a zero-weight policy ablation. See `training/evaluation.json`.
- Explicit reward-shaping ablation: same architecture, seed and 8,000 training episodes, with/without added challenge/load/repetition reward. See `training/reward_ablation.json`. Both simulators still contain challenge-dependent learning. Report negative or mixed differences as well as positive ones.

```sh
python3 training/train.py --episodes 8000 --seed 42
python3 training/evaluate.py --learners 100
python3 training/train.py --episodes 8000 --seed 42 --no-struggle --output /tmp/policy-no-struggle.json
python3 training/evaluate.py --learners 100 --ablation /tmp/policy-no-struggle.json
```

Use an appropriate temporary path on Windows. Training writes policy.json only when the default output is used; candidate retraining in GitHub still does not auto-promote or deploy a model. CI now installs the pinned training dependency.

Existing V2 documentation describes the previous Q-table and fixed map. This guide supersedes those algorithm/assessment sections for V3; account provisioning, database operations and content authoring remain as before.
