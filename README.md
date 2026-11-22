# Personalized Learning Path Agent — Version 3

A browser-based adaptive Python learning platform. A trained Double DQN policy recommends the next learning activity based on each student's evolving progress.

**Team:** Vanshika, Vasvi, Chaitali, Srishti

- Demo: https://huggingface.co/spaces/Chaitali-24csu246/personalized-learning-path
- Deployment guide: see the Cutover Document (Azure Static Web Apps)
- Upgrade notes: [UPGRADE_V3.md](UPGRADE_V3.md)

Login requires the existing Supabase project and provisioned accounts. No default passwords are included. See [SETUP_V2.md](SETUP_V2.md) for backend setup.

## What's new in V3

- A trained **Double DQN** scores eligible learning activities, replacing the V2 Q-table policy.
- Starting assessment results shape the learner's initial recommendations.
- Scored MCQ and coding attempts update shared topic progress.
- Conceptual understanding and coding performance are tracked separately.
- Practice adapts activity type and difficulty within a topic.
- The learning map updates from current progress; future steps are provisional.
- Evaluation compares the DQN against simpler recommendation approaches.

The course content, account system and Supabase database are unchanged from V2. No database recreation is needed.

## Features

- 20 Python units, from expressions to OOP, generators, decorators, testing and async.
- 240 MCQs (180 practice, 60 reserved for assessment) and 60 coding exercises with automated output tests and two hint levels.
- Lessons, worked examples, common mistakes and prerequisite metadata.
- Executable coding practice in the browser (Pyodide in a Web Worker, 8-second timeout, stop button, output cap).
- Authenticated student accounts with private progress and code drafts, plus export/import backups.
- Protected administrator console for catalog management, topic requests and video links.

## How the recommender works

The Double DQN runs entirely in the browser from a frozen, saved policy (`web/policy.json`). It ranks eligible activities using the learner's current topic estimates. Student answers update those estimates, **not** the model weights.

Prerequisites, scoring, content filtering and within-family item selection are deterministic application logic. Reading a lesson does not raise mastery, and repeated or assisted attempts do not earn unrestricted credit.

The policy was trained on a simulated learner. Evaluation results (`training/evaluation.json`) show how it compares with baselines in simulation. They do not establish educational effectiveness with real students.

## Run locally

Requires Python 3.10+ and a running Supabase project.

```
python3 start.py --port 8001
```

On Windows use `python start.py --port 8001`. Open the address printed by the script. Don't open `web/index.html` directly, since the app loads modules over HTTP. Coding practice downloads Pyodide on first use, so it needs internet.

## Deploy (Azure Static Web Apps)

1. Confirm `main` contains V3 (`UPGRADE_V3.md`, `web/engine.mjs`, `candidate-dqn-v3` in `web/policy.json`).
2. Confirm `web/config.js` holds the Supabase project URL and **public** anon key. Never commit secret or service-role keys.
3. Create a Static Web App from this repo: branch `main`, build preset Custom, app location `web`, API and output locations blank.
4. In the generated workflow, set `app_location: "web"`, `api_location: ""`, `output_location: ""`, `skip_app_build: true`.
5. Open the generated HTTPS URL once the workflow succeeds.

Make sure the Supabase project is running before testing login. Hosting changes don't require migrating the database.

## Development and checks

```
python -m unittest discover -s tests -v
npm run check
npm test
python training/evaluate.py --learners 100
```

Python training and tests use the standard library only. JavaScript checks need Node 20+. Node isn't needed to use the website. Content is authored in `scripts/build_content.py` and generated into `web/content.json`. If content changes, the policy must be retrained and re-evaluated before release. See UPGRADE_V3.md for the training workflow.

## Structure

- `web/`: static site, content, trained policy, browser inference, Python worker
- `training/`: simulator, training, behaviour checks and evaluation
- `scripts/`: content generation and packaging
- `tests/`: solution, question, simulator and recommendation tests
- `backend/`: Supabase-related setup
- `.github/workflows/`: CI and deployment workflows

## Limitations

- No chatbot, teacher portal or PDF-generated courses.
- Only Python is implemented. Other subjects are marked "Coming later".
- Coding tests check outputs, not whether a specific technique was used.
- The in-browser runner is for personal practice, not secure grading.
- Runtime depends on an external CDN for Pyodide.
- Optional checks reuse a reserved item set, so repeat scores may reflect familiarity.
- Deployment shows that the platform works. It does not demonstrate learning gains.
