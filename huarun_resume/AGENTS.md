# Repository Guidelines

## Project Structure & Module Organization

This repository is currently an empty scaffold for `huarun_resume`. Keep the project root small and predictable: place application source under `src/`, tests under `tests/`, static assets under `assets/`, and project documentation under `docs/`. If the project becomes a single-page resume site, prefer clear feature folders such as `src/components/`, `src/pages/`, and `src/styles/`.

## Build, Test, and Development Commands

No build system, package manifest, or test runner has been added yet. After choosing a stack, document the exact commands here before relying on them in reviews or automation.

Useful current checks:

- `git status` shows changed, staged, and untracked files.
- `git diff --check` catches trailing whitespace and common patch formatting issues.
- `find . -maxdepth 3 -type f | sort` gives a quick view of the scaffold while the repo is small.

## Coding Style & Naming Conventions

Follow the conventions of the framework once one is introduced. Until then, use two-space indentation for web files, four-space indentation for Python if added, and descriptive lowercase file names with hyphens for static assets, for example `assets/profile-photo.jpg`. Prefer small modules with direct names such as `resume-header`, `work-experience`, or `contact-links`.

## Testing Guidelines

Add tests with the first non-trivial behavior. Keep test files near the behavior they cover or under `tests/`, using names such as `resume-header.test.ts` or `test_resume_parser.py`. Each bug fix should include a regression test when the chosen stack supports it. Document coverage expectations here once the test runner exists.

## Commit & Pull Request Guidelines

There is no existing commit history, so use concise imperative commit messages: `Add resume layout scaffold`, `Fix contact link styling`, or `Document deployment steps`. Pull requests should describe the change, mention how it was tested, link related issues when available, and include screenshots for visible UI changes.

## Security & Configuration Tips

Do not commit secrets, private contact exports, or generated credentials. Use `.env` for local configuration once needed, and commit only a safe example such as `.env.example`.
