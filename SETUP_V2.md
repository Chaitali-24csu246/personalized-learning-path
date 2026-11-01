# Version 2 — connect accounts before deployment

This is a complete source package, **not an already configured cloud service**. Without your Supabase project URL and public key the website intentionally shows a setup screen. There is no insecure local-login bypass and no shared/default password. Existing Python course/training files remain included. PDF uploads and chatbot features are not implemented.

## 1. Preserve your current repository

Make a backup or commit your current work. Extract this ZIP elsewhere and copy its **contents** into the existing repository folder. Do not create another nested personalized-learning-path folder. Keep your repository’s existing `.git` directory. Replace matching app files and add the new backend/configuration files. Preserve any team changes by reviewing the diff before committing.

Export your old browser-local progress from version 1 before replacing it. After signing in to version 2, import that JSON backup into the correct student account. Nothing automatically assigns old shared-browser progress to a student.

## 2. Create the database/authentication project

Create your own Supabase project. In its SQL Editor, run **backend/schema.sql once** on a new project. Do NOT run ci-auth-stub.sql or test_rls.sql on the real project; those are for a disposable CI database.

Disable public new-user signups in the project's Auth settings: this version provisions accounts through an administrator. Enable appropriate password strength/rate-limit settings. Do not expose the project legacy service_role JWT key in the app, GitHub files, logs or messages.

Schema tables:
- `profiles`: account ID, username, display name and immutable-to-students role.
- `student_progress`: a private JSON progress document for each account, with version checks.
- `topic_requests`: each student's requests; administrators can review/update their status.
- `course_catalog`: administrator-published course/topic/activity overrides.

Row-level policies restrict student reads to their own progress and requests. Admins can see requests, not private progress. Only administrator-only SQL functions can publish a catalog. Role assignment is done by the operator script, never by the browser.

## 3. Create the five accounts

In a terminal in the project folder:

```sh
python3 backend/provision.py
```

On Windows use `python` instead of `python3`. The script prompts for your project URL and legacy service_role JWT key (hidden input), then individual passwords for:

- vanshika
- srishti
- chaitali
- vasvi
- admin

Set a different password of at least 12 characters for each account. Passwords are never printed or saved to files. Deliver them privately; each student can change their own password after login. The script creates users and profiles; rerunning it skips already provisioned profiles. If interrupted between creating an Auth user and its profile, reconcile that one account in the Supabase dashboard before rerunning. Do not delete existing student accounts to repair configuration.

The authentication provider internally uses `username@students.learningpath.invalid` aliases. These are not real mailboxes, so email password-reset delivery is intentionally not offered. Forgotten passwords are reset by the operator with:

```sh
python3 backend/provision.py --reset vasvi
```

The admin account signs in through the SAME login screen and is routed to the admin console based on its server-stored role. No admin item appears in the student sidebar. Students cannot self-promote through the API.

## 4. Configure and run locally

Run:

```sh
python3 scripts/configure.py
python3 start.py
```

Enter the project URL and the **PUBLIC anon/publishable key** when asked. The configuration script rejects secret keys and service-role JWTs. It writes `web/config.js`; its public connection values are intended to be visible in the browser. Database security comes from Auth and row-level policies, not from hiding the public key.

Internet access is required for Supabase, the authentication SDK, video playback and the first Python runtime download. If a save fails, the app says **Not saved**, keeps pending changes in memory, and offers export/save retry. Do not close the tab before saving or exporting. Concurrent edits from another tab/device produce a conflict rather than silently overwriting progress; export a backup and reload before continuing. Use one active editing tab per account.

## 5. Verify against the real project

Before enabling public deployment, personally complete these checks:

1. Sign in as each student; record one activity; sign out; check another account starts with its own progress.
2. Sign back in on a second browser/device and confirm the first activity appears only in its owner's account.
3. Change one student password and verify old/new login behaviour.
4. Submit a topic request. Verify the student sees it and admin can update its status.
5. Confirm a student's direct API attempts cannot read another account's progress, update roles or publish catalog changes.
6. Sign in as admin; stage a topic/video update, publish, then reload as student to verify it. Export a catalog backup.
7. Try simultaneous saves on two tabs and verify the conflict warning. Check offline saving reports failure rather than success.
8. Run a coding exercise, a video, a quiz and a checkpoint on the final hosted URL.

Local unit tests use mocks for network operations. They do not prove your live Supabase configuration is correct. The CI pipeline additionally runs real PostgreSQL role-policy tests in a disposable database with a minimal Auth stub. Passing CI still does not test the production project's Auth configuration or email-alias account provisioning.

## 6. Admin workflows

- **Add/update course:** enter its ID, title and description. It stays Coming later until a topic is added.
- **Add/update topic:** choose an existing topic or edit the new-topic JSON. Save to draft, then publish. Include `courseId` (`python` for the current course). Categories currently use the three supplied syllabus stages. This remains Python-first; it is not a full multi-language authoring platform.
- **Remove topic:** choose it and stage removal. Removal is blocked if another topic depends on it; remove/update dependencies first. The introductory topic is retained. Old student history is preserved.
- **Update question bank:** import a JSON activities array or a content.json-style object containing activities. Existing IDs are replaced and new ones are added. The client validates structure, answer ranges, IDs and prerequisites. The administrator must review content and execute reference solutions before publishing.
- **Publish:** validates and saves draft changes to the database with a revision check. Conflicting admin edits must be reloaded/reconciled.
- **Video:** use a YouTube watch URL or youtu.be URL in `videoUrl`; the app constructs the safe embed itself. Other iframe URLs are rejected.
- **Requests:** change the request status to submitted/reviewing/planned/closed; status saves immediately.

Admin draft changes are held in memory until published. Export a draft backup if you need to leave before publishing. There is no visual WYSIWYG editor: topic editing is a structured JSON form and question updates use JSON import. Existing source files are unaffected by database catalog edits.

## 7. CI/CD and Pages

Upload the complete source, including `.github/workflows`. CI runs Python/JS tests, SQL access-policy tests, content reproducibility checks, simulated policy evaluation and packaging.

In GitHub repository settings:
- Pages publishing source: GitHub Actions.
- Repository variable `SUPABASE_URL`: your public project URL.
- Repository variable `SUPABASE_ANON_KEY`: your PUBLIC anon/publishable key.
- Repository variable `ENABLE_PAGES`: set to `true` only after setup/live checks above.

The deploy job generates public `web/config.js` from these variables and refuses to deploy without them. Never add the service-role key as one of these values. A candidate-policy retraining workflow remains separate and never auto-replaces the deployed model.

## 8. What changed and what remains limited

Added real account authentication, private server persistence, password change, role-protected admin, catalog draft/publish operations, centrally saved topic requests, and optional video playback. Fixed durable assistance flags and independent corrected coding retries (without unlimited repeat credit). Added concurrency checks to saves.

The original 20-topic RL policy is unchanged. Newly added or edited topics are excluded from that learned policy until validated; a deterministic fallback is used where needed. Exact question choice, scoring, prerequisites and admin editing are not RL. New question imports require pedagogical and solution review. Browser coding tests are practice checks, not tamper-proof grading.

Video metadata includes direct resources for 15 topics. The other 5 topics have explicitly labelled YouTube search links, which an administrator can replace with a reviewed direct video URL. Video availability, regional restrictions and embedding permissions can change.

The generated files have been checked locally, but no live Supabase project or remote GitHub workflow was executed during this update. Complete the setup and live checks before describing the deployment as verified.
