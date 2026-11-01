# Learning Path

A browser-based Python learning platform with an adaptive activity policy, a syllabus sidebar, lessons, MCQs, executable coding exercises and a learning map. Other subjects are visibly marked “Coming later”.

## Start here — no notebook, API key or npm install needed

1. Extract the ZIP. Open the **personalized-learning-path** folder.
2. Install Python 3.10 or newer if you do not have it.
3. Open a terminal in this folder and run:

```sh
python start.py
```

On macOS/Linux use `python3 start.py`. On Windows you may use `py -3 start.py` or double-click `START_WINDOWS.bat`. The site opens at **http://localhost:8000**. Keep the terminal open. Stop it with Ctrl+C. If the port is occupied, use `python start.py --port 8001`.

Do not double-click `web/index.html`: the app loads JSON and modules over HTTP. Python execution in the browser downloads pinned Pyodide 0.27.7 from jsDelivr on first use. **Internet is required for coding execution.** Lessons, MCQs and the saved policy are included locally. The app runs user code in a Web Worker with an eight-second execution timeout, a stop button and an output cap. This is a personal practice runner, not a secure competitive grading service. Test expectations are inspectable in the browser. No server executes student code.

## What is included

- 20 Python units from expressions through OOP, generators, decorators, context managers, testing and async.
- 240 MCQs: 180 practice questions and 60 reserved assessment questions. Some are related input variants from the same code-tracing family; these are not 240 unrelated concepts.
- 60 coding exercises, each with four automated output tests, two hint levels and a reference solution.
- Original concise topic lessons, worked examples, common mistakes, prerequisite metadata and official-documentation links. This is a substantial course foundation, not a substitute for an entire textbook or educator review.
- A mixed practice workspace with separate MCQ/coding filters and difficulty selection.
- Grey/red/yellow/green syllabus indicators, with text labels. MCQ and coding estimates are separate.
- A trained Q-learning policy from **8,000 simulated episodes** (45 steps each), runnable training/evaluation source, and baseline comparisons.
- Browser-local progress, code drafts, export/import backups and reset. No user accounts or cross-device sync.
- CI validation, optional GitHub Pages deployment, downloadable CI source artifact and a manual candidate-policy training pipeline.

## Upload to GitHub

Create an empty repository named `personalized-learning-path` (avoid adding an initial README if you will push this folder). GitHub Desktop is easiest: **File → Add local repository**, choose the extracted folder, choose **create a repository here** if prompted, then commit all files and **Publish repository**. Check the repository root contains `README.md`, `web/`, `training/` and `.github/workflows/`.

Alternatively, in the extracted project folder:

```sh
git init -b main
git add .
git commit -m "Build adaptive Python learning platform"
git remote add origin https://github.com/YOUR_USERNAME/personalized-learning-path.git
git push -u origin main
```

Replace YOUR_USERNAME. Authenticate using GitHub’s normal browser/Git credential flow; never put tokens in source files. **Do not upload just the ZIP**: GitHub needs its extracted contents, including the `.github` folder. Drag-and-drop uploads may omit hidden folders, so GitHub Desktop or `git add .` is safer.

## Enable deployment once you are ready

1. Open repository **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. Under **Settings → Secrets and variables → Actions → Variables**, add repository variable `ENABLE_PAGES` with value `true`.
3. Open **Actions → Test and deploy Learning Path → Run workflow**, or push a commit to `main`.
4. Tests run first. Deployment runs only after they pass. GitHub provides the final URL in the deployment job.

Before step 2, deployment is deliberately skipped and CI still runs. This avoids a failing Pages deploy before your repository is configured. GitHub Pages availability depends on your repository/account settings. The app uses relative asset URLs, so repository subpaths work. You do not need a backend, secret API key or paid hosting service for this version.

## Development and checks

Python training/tests use the standard library only. JavaScript checks require Node 20+; the app itself does not require Node installed on a student’s computer.

```sh
python -m unittest discover -s tests -v
npm run check
npm test
python training/evaluate.py --learners 100
```

Edit authored content in `scripts/build_content.py`, then run it to regenerate `web/content.json`. Run checks. A changed content file requires retraining to refresh the saved policy’s content hash:

```sh
python scripts/build_content.py
python training/train.py --episodes 8000 --seed 42
python training/evaluate.py --learners 100
python -m unittest discover -s tests -v
```

Create a fresh distributable ZIP with `python scripts/package.py`. You may ignore Node commands when simply using the website.

## How the adaptive component works

`training/engine.py` implements a partially observed simulated learner. Conceptual and practical hidden knowledge vary separately, as do learning rates, forgetting, guessing and slips. Hidden knowledge is **not** supplied as policy input. The shared Q table ranks eligible `(topic, activity type, difficulty)` candidates using discretised observed MCQ/coding estimates, repeated failures, a review flag, session phase and whether a lesson was read. The temporal-difference update bootstraps future value (gamma 0.93), rather than selecting only immediate reward.

This is a compact **state abstraction**, not a full Markov description of human learning. Simulated reward uses hidden learning gain, a per-step cost and terminal gain. These rewards are training assumptions, not measurable claims about a real student. The website uses the frozen saved policy; it updates learner estimates, not Q values, after student responses. Prerequisites, scoring, eligible content filtering and within-family item selection are deterministic application logic, not learned by RL. Unseen/exhausted states have an explicit fallback. Changing Q values changes recommendations; the JS integration test checks this.

In the website, reading a lesson does not increase mastery. Assisted attempts and successfully completed question families do not repeatedly raise it. MCQ success does not update coding ability. Easy questions have a lower evidence ceiling. These estimates are simple heuristics rather than validated psychometric scores. The finite bank and help use can leave a learner needing more independent evidence; green status is never guaranteed by completion alone.

`training/evaluation.json` compares RL, random, rule-based and prerequisite-constrained fixed paths on held-out seeds, with two simulator parameter settings. It reports both positive and negative results. It does not establish real educational benefits or superiority to commercial platforms. Simulated hidden mastery/retention is distinct from actual learner test scores. The UI’s optional checks reuse a reserved item set, so repeat scores can reflect familiarity. They are not independent pre/post experimental forms.

## Structure

- `web/`: static website, content, trained policy, browser inference and Python worker.
- `training/`: simulation, Q-learning, baseline evaluation and saved evaluation results.
- `scripts/`: content authoring/generation and ZIP packaging.
- `tests/`: reference-solution, question-answer, simulator and recommendation tests.
- `.github/workflows/`: CI/CD and optional retraining.
- `start.py`: cross-platform local server.

## Current boundaries

No chatbot, video scraping, accounts, cloud database or teacher portal. Browser storage can be cleared; export a backup. Runtime loading depends on the external CDN. Coding checks test outputs, not whether a solution truly uses a requested OOP/recursion technique; those need code review. No protected third-party question bank was copied. Additional subjects need reviewed content, scoring rules and validation of the learning model; a placeholder is not an implemented course.
