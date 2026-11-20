# Prompt Manager — Agent Build Brief

Paste the brief below into one coding agent with the project folder or intended GitHub repository selected. It is written for Antigravity, Mousebot, or Gemini without assuming identical capabilities. Feature choices below are proposed defaults.

---

Act as the lead developer for my desktop prompt manager. I direct the product; you handle implementation, setup, debugging, verification, documentation, and preparing the GitHub project. Deliver working software, not only a plan.

## Goal

Build a Windows desktop application where I can save and organize reusable chatbot prompts, instruction prompts, and skill text, then quickly find and copy them. Use the working title **Prompt Library** until I choose a final name.

The application itself must work offline. Do not require an AI model, API key, account, subscription, or hosted backend. AI is being used to develop the app; AI is not an app feature.

## Begin with the actual environment

1. Inspect the selected project, its instructions, Git status, and existing implementation before changing it. Preserve unrelated work.
2. Determine whether you can edit files, run terminal commands, launch the app, and build Windows packages. Check repository access separately. A GitHub connection is not proof of local execution access.
3. If the repository is empty, choose a practical, maintained desktop framework and storage approach. Verify current official documentation before selecting versions or setup commands. Prefer a small, straightforward project over a complex architecture.
4. Briefly state the architecture and milestones, record them in the repository, then start implementation. Do not stop after presenting a plan.
5. If you cannot execute builds, still implement what your environment supports and provide exact handoff steps. Clearly distinguish code produced, checks actually run, and checks still needed.

## Version 1: the useful core

Create a real application with:

- Create, edit, duplicate, and delete prompts. Make deletion recoverable through trash.
- Fields for title, optional description, prompt body, category, tags, favorite status, and creation/update timestamps.
- User-managed categories, with an Uncategorized fallback. Prompts can have multiple tags.
- Search across title, description, body, and tags, with category and favorite filters.
- One-click copy of the exact prompt body, with visible success or failure feedback.
- Local persistent storage that survives closing and reopening the application.
- Import and export of a versioned JSON backup, including prompts and organization metadata. Validate before modifying saved data; imports must not silently overwrite existing prompts.
- A few clearly identified sample prompts for first launch, which the user can remove.

Use a comfortable desktop layout: category sidebar, searchable prompt list, and editor. Include readable typography, keyboard navigation, helpful empty states, and clear save/error feedback. Preserve whitespace and code in prompts. Protect unsaved changes when navigating or closing. Treat stored text as data; displaying a prompt must never execute its contents.

Keep the first release focused. Defer cloud sync, accounts, chatbot integrations, marketplaces, and AI generation.

## Version 2: reusable templates

After the core is working:

- Support named placeholders such as {{project_name}} and {{language}}.
- Show a form for their values before generating a copy.
- Apply repeated placeholders consistently and flag missing values.
- Keep the saved template unchanged when copying a filled version.
- Support importing plain text and Markdown as prompts and exporting selected prompts as Markdown.
- Label exported instruction text clearly; do not claim compatibility with a particular agent's skill format unless that format is explicitly implemented and verified.

## Data and repository boundaries

Store the user's collection in an appropriate per-user application data location, outside the source checkout. Keep personal prompts, local databases, backups, credentials, and generated build output out of Git. Track useful sample data and dependency lockfiles.

Use durable saves and handle invalid or unreadable data without silently replacing it. Back up existing data before a migration that could change it. Document where data is stored and how users can back it up.

Keep the implementation understandable: separate persistence, template processing, and interface concerns without adding unnecessary services.

## Work through milestones

1. **Foundation:** project setup, runnable desktop shell, data model, storage, and sample data.
2. **Core:** editing, organization, search, favorites, copy, trash, and JSON backup/restore.
3. **Templates and polish:** placeholder flow, Markdown/text exchange, shortcuts, and interface refinement.
4. **Distribution:** clean builds, Windows packaging, documentation, and GitHub preparation.

Continue autonomously within this scope. Resolve routine implementation choices yourself. After each milestone, give a short update with what works, what you verified, and the next step. Ask only when a missing product decision, missing access, or a genuinely destructive action prevents progress.

Keep progress and remaining work in a concise project status file so another session can continue from the current state.

## Verification that matters

Verify real behavior, especially:

- Create and edit a prompt, restart the app, and confirm the saved content and metadata remain intact.
- Combine search and filters and confirm correct results.
- Delete and restore a prompt.
- Copy text containing Unicode, line breaks, and code without changes.
- Export and import into a separate test collection; compare content and metadata.
- Reject malformed imports without losing existing data.
- Check repeated and missing template variables without changing the stored template.
- Launch the packaged Windows app and verify editing, persistence, and copying.

Use focused automated tests for persistence, import/export validation, and template processing, plus practical interface checks. Run relevant build and quality checks. Report failures honestly. If no Windows environment is available, prepare an appropriate Windows build workflow and identify packaged-app verification as pending; do not claim that a workflow file alone proves the build works.

## GitHub and release deliverables

Prepare:

- Source code with a clear project structure and sensible commits.
- A README explaining the app, current features, development setup, and installation.
- Reproducible setup/build commands, dependency lockfiles, and a version number.
- A Windows package when the environment supports producing it.
- A changelog, contribution guidance, and appropriate build checks.
- Screenshots only from the actual running application.
- A documented license decision left pending until I choose the license.

Use the explicitly selected GitHub repository and available permissions. Do not guess my account, overwrite another project, or force-push. Push and publish within the access and repository scope I have supplied. If the target repository, authentication, or publication details are missing, finish the local work and identify exactly what is needed to publish.

End with a concise handoff: what was built, what was tested, where to run or download it, the repository/release URL if actually published, and any remaining limitations.

Start now by inspecting the project and your capabilities, recording a short plan, and implementing the foundation.

