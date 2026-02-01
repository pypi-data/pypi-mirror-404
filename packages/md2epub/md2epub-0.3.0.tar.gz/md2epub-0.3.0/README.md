# md2epub

**md2epub** is a helper library and CLI tool designed to convert Markdown text into professional, publish-ready EPUB files. It specifically targets formatting standards suitable for KDP (Kindle Direct Publishing), ensuring strict ordering of content (Cover, Title, Copyright, TOC, Dedication, Chapters).

## Features

* **Project Scaffolding**: Quickly initialize a book directory with a standard structure using Cookiecutter templates.
* **Markdown to EPUB**: Converts Markdown content into XHTML with a generated navigation structure.
* **KDP-Ready Styling**: Includes a CSS template optimized for e-readers, handling fonts, margins, and scene breaks.
* **Custom Formatting**: specific support for novel formatting:
* `xxx` on a single line creates a centered **Scene Break**.
* `***` on a single line creates a centered **Asterisk Break**.

---

## Guide for Writers

### 1. Installation

Ensure you have Python 3.12 or higher installed.

```bash
pip install md2epub

```

### 2. Creating a New Book

To start a new project, use the `init` command. This creates a folder with all the necessary configuration files and templates.

```bash
md2epub init my_new_book

```

You will be prompted for basic details (Book Name, Author Name, Dedications, etc.) which are used to configure the project.

### 3. Writing Your Content

Navigate to your new book directory. You will see several markdown files (e.g., `chapter_01.md`, `title.md`). Write your book using standard Markdown.

**Formatting Tips:**

* **Chapters:** Start chapters with a header `# Chapter Title`.
* **Scene Breaks:** To insert a visible break in the text, place `xxx` on its own line.
* **Asterisks:** To insert a decorative break, place `***` on its own line.

### 4. Configuration (`metadata.yaml`)

The `metadata.yaml` file controls the build process. You must list every file you want to include in the EPUB here.

```yaml
title: "My Great Novel"
author: "Jane Doe"
language: en
cover_image: cover.png
front_matter:
  - title.md
  - copyright.md
  - dedication.md
chapters:
  - chapter_01.md
  - chapter_02.md

```

### 5. Compiling the EPUB

When you are ready to generate your book:

```bash
md2epub compile my_new_book

```

This will generate an `.epub` file in the current directory.

---

## Guide for Developers

### Development Setup

1. Clone the repository.
2. Install the package in editable mode with development dependencies.

```bash
python -m pip install --upgrade pip
pip install -e .[dev]

```

### Running Tests

The project uses `pytest` for testing. A custom script `scripts/run_tests.py` is provided to run tests and enforce coverage thresholds.

```bash
python scripts/run_tests.py

```

* **Failure Threshold:** The build fails if more than 20% of tests fail.
* **Coverage Threshold:**
* Codebase < 1000 lines: 60% coverage required.
* Codebase >= 1000 lines: 80% coverage required.



### Project Architecture

The codebase follows the SOLID principles, separating concerns into distinct modules:

* **`src/md2epub/cli.py`**: Handles user interaction and commands (`init`, `compile`).
* **`src/md2epub/epub_builder.py`**: The core logic class (`EpubBuilder`) responsible for assembling the book, managing metadata, and ensuring strictly ordered spine items (Cover -> Front Matter -> TOC -> Chapters).
* **`src/md2epub/converter.py`**: Handles text processing, converting Markdown to HTML and injecting custom classes for separators.
* **`src/md2epub/css_template.py`**: Contains the `KDP_CSS` string used to style the EPUB.

### Release Workflow

The project uses GitHub Actions for CI/CD.

* **Pull Requests**: PRs to `main` must come from `dev`.
* **Versioning**: Semantic versioning is automated based on PR labels. When a PR is merged to `main`:
* Label `bump:major` → Major increment.
* Label `bump:patch` → Patch increment.
* Default (no label/other) → Minor increment.


* **Publishing**: Releases are automatically published to PyPI and GitHub Releases upon merge.

### License

This project is licensed under the MIT License.