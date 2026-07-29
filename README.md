# ✅ To-Do List App

A clean, full-featured To-Do List web app built with **Python**, **Streamlit**, and **Supabase** (Postgres). Add, edit, complete, filter, and search tasks — with priorities, categories, due dates, and persistent cloud storage.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.60+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Supabase](https://img.shields.io/badge/Supabase-Postgres-3ECF8E?style=flat&logo=supabase&logoColor=white)](https://supabase.com/)
[![Tests](https://img.shields.io/badge/tests-30%20passing-brightgreen?style=flat)](#-running-tests)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat)](#-license)

<p align="center">
  <img src="https://img.shields.io/badge/status-active-success" alt="status">
  <img src="https://img.shields.io/badge/made%20with-%E2%9D%A4%EF%B8%8F-red" alt="made with love">
</p>

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Setup Guide](#-setup-guide)
  - [1. Clone the repo](#1-clone-the-repo)
  - [2. Create a virtual environment](#2-create-a-virtual-environment)
  - [3. Install dependencies](#3-install-dependencies)
  - [4. Set up Supabase](#4-set-up-supabase)
  - [5. Configure environment variables](#5-configure-environment-variables)
  - [6. Run the tests](#6-run-the-tests)
  - [7. Run the app](#7-run-the-app)
- [Running Tests](#-running-tests)
- [Deployment](#-deployment-streamlit-community-cloud)
- [Troubleshooting](#-troubleshooting)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## ✨ Features

- ➕ Add tasks with **priority** (Low / Medium / High), **category**, and optional **due date**
- ✅ Mark tasks complete/incomplete with a single click
- ✏️ Inline editing of any task
- 🗑️ Delete individual tasks, or bulk-delete completed tasks / all tasks
- 🔍 Search tasks by keyword
- 🎯 Filter by status, priority, and category
- ↕️ Sort by creation date, priority, or due date
- ⚠️ Automatic overdue detection and highlighting
- 📊 Live stats dashboard (total, active, completed, overdue, completion rate)
- ☁️ Cloud persistence via Supabase — your tasks survive restarts and are accessible from anywhere

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| UI | [Streamlit](https://streamlit.io/) |
| Language | Python 3.10+ |
| Database | [Supabase](https://supabase.com/) (hosted Postgres) |
| Testing | pytest + Streamlit's `AppTest` framework |
| Deployment | Streamlit Community Cloud |

---

## 📁 Project Structure

```
todo-app-supabase/
├── .streamlit/
│   └── secrets.toml.example   # Template for Streamlit Cloud secrets
├── app.py                     # Streamlit UI
├── task_manager.py            # Core logic — talks to Supabase
├── schema.sql                 # Database schema (run once in Supabase)
├── requirements.txt           # Python dependencies
├── test_task_manager.py       # 23 unit tests (mocked DB, no network needed)
├── test_app_integration.py    # 7 integration tests (runs the real app.py)
├── .env.example                # Template for local credentials
└── .gitignore
```

---

## ✅ Prerequisites

Make sure you have these installed before starting:

- [Python 3.10+](https://www.python.org/downloads/) (check "Add to PATH" during install on Windows)
- [VS Code](https://code.visualstudio.com/) with the **Python extension** (Microsoft)
- A free [Supabase](https://supabase.com/) account
- A [GitHub](https://github.com/) account (for deployment)

---

## 🚀 Setup Guide

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/todo-app-supabase.git
cd todo-app-supabase
```

### 2. Create a virtual environment

<details>
<summary><strong>Windows (PowerShell)</strong></summary>

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

> If you get an execution policy error, run this once, then try activating again:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
</details>

<details>
<summary><strong>Windows (Command Prompt)</strong></summary>

```cmd
python -m venv venv
venv\Scripts\activate.bat
```
</details>

<details>
<summary><strong>Mac / Linux</strong></summary>

```bash
python3 -m venv venv
source venv/bin/activate
```
</details>

You'll know it worked when you see `(venv)` at the start of your terminal prompt. In VS Code, also select this interpreter via `Ctrl+Shift+P` → **Python: Select Interpreter**.

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install pytest
```

| Package | Purpose |
|---|---|
| `streamlit` | Builds the web UI |
| `supabase` | Python client for the Supabase database |
| `pytest` | Runs the automated test suite (dev-only) |

### 4. Set up Supabase

1. Go to [supabase.com](https://supabase.com) → sign up → **New Project**
2. Choose a name, database password, and region → wait ~2 minutes for provisioning
3. Open **SQL Editor → New Query**, paste in the full contents of [`schema.sql`](./schema.sql), and click **Run**
   - You should see `Success. No rows returned`
   - This script is **safe to re-run** any number of times without errors
4. Go to **Project Settings → API** and copy:
   - **Project URL**
   - **anon public** key (a long string starting with `eyJ...`)

### 5. Configure environment variables

You need `SUPABASE_URL` and `SUPABASE_KEY` set before running the app.

<details>
<summary><strong>Windows (PowerShell)</strong></summary>

```powershell
$env:SUPABASE_URL="https://your-project-ref.supabase.co"
$env:SUPABASE_KEY="your-anon-public-key"
```

Verify:
```powershell
echo $env:SUPABASE_URL
echo $env:SUPABASE_KEY
```
</details>

<details>
<summary><strong>Windows (Command Prompt)</strong></summary>

```cmd
set SUPABASE_URL=https://your-project-ref.supabase.co
set SUPABASE_KEY=your-anon-public-key
```

Verify:
```cmd
echo %SUPABASE_URL%
echo %SUPABASE_KEY%
```
</details>

<details>
<summary><strong>Mac / Linux</strong></summary>

```bash
export SUPABASE_URL="https://your-project-ref.supabase.co"
export SUPABASE_KEY="your-anon-public-key"
```

Verify:
```bash
echo $SUPABASE_URL
echo $SUPABASE_KEY
```
</details>

> ⚠️ **Common mistake:** these commands only work in the terminal type they're written for. `$env:VAR=...` is PowerShell-only; `export VAR=...` is Mac/Linux-only; `set VAR=...` is Command Prompt-only. Mixing them causes "filename, directory name, or volume label syntax is incorrect" errors on Windows. Check which terminal is active in the VS Code dropdown before running these.

> ⚠️ Double-check you copied the **anon public** key — not the project reference, not a region code, not the service_role key. It's a long JWT string starting with `eyJ`.

These variables reset every time you close the terminal — you'll need to re-run them in each new session (or set up a `.env` file with `python-dotenv` as a future enhancement).

### 6. Run the tests

```bash
python -m pytest test_task_manager.py test_app_integration.py -v
```

Expected result: **`30 passed`**. These tests use an in-memory fake database, so they'll pass even before your Supabase credentials are set — this confirms your code and libraries are installed correctly.

### 7. Run the app

```bash
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`.

**Manually verify:**
- [ ] Add a task from the sidebar
- [ ] Check it off — stats update
- [ ] Edit a task's text
- [ ] Delete a task
- [ ] Refresh the browser — your task is still there
- [ ] Check **Supabase → Table Editor → tasks** — the task appears as a real row

---

## 🧪 Running Tests

| File | What it covers |
|---|---|
| `test_task_manager.py` | 23 unit tests on core CRUD logic, validation, filtering, and stats — using a mocked Supabase client |
| `test_app_integration.py` | 7 integration tests that run the real `app.py` through Streamlit's `AppTest` framework, simulating clicks and form submissions |

Run everything:
```bash
python -m pytest test_task_manager.py test_app_integration.py -v
```

Run just one file:
```bash
python -m pytest test_task_manager.py -v
```

---

## ☁️ Deployment (Streamlit Community Cloud)

1. Push this repo to GitHub (already done if you're reading this on GitHub 🎉)
2. Go to [share.streamlit.io](https://share.streamlit.io) → sign in with GitHub
3. **Create app** → **Deploy a public app from GitHub**
4. Select this repo, branch `main`, main file path `app.py` → **Deploy**
5. Once deployed, go to your app's **⚙️ Settings → Secrets** and paste:
   ```toml
   SUPABASE_URL = "https://your-project-ref.supabase.co"
   SUPABASE_KEY = "your-anon-public-key"
   ```
6. Save — the app redeploys automatically with a live public URL

> Your `.gitignore` already excludes `.env` and `.streamlit/secrets.toml`, so real credentials never get committed to GitHub.

---

## 🩹 Troubleshooting

<details>
<summary><strong>"policy already exists" error when running schema.sql</strong></summary>

You likely ran the script twice. Use the version of `schema.sql` in this repo — it includes `drop policy if exists ...` before creating the policy, making it safe to re-run.
</details>

<details>
<summary><strong>App shows "Setup required: could not connect to the database"</strong></summary>

Your `SUPABASE_URL` / `SUPABASE_KEY` environment variables aren't set in the current terminal session. Re-run the commands from [Step 5](#5-configure-environment-variables) in the same terminal you're launching `streamlit run app.py` from.
</details>

<details>
<summary><strong>App shows "Could not reach the database"</strong></summary>

Usually means one of:
- The URL or key has a typo, or you copied the wrong key (double-check it's the **anon public** key)
- The `tasks` table hasn't been created yet — re-run `schema.sql`
</details>

<details>
<summary><strong>"filename, directory name, or volume label syntax is incorrect" (Windows)</strong></summary>

You're mixing terminal syntaxes. `$env:VAR="..."` only works in PowerShell; `set VAR=...` only works in Command Prompt. Check which shell is active (shown in the VS Code terminal dropdown) and use the matching syntax from [Step 5](#5-configure-environment-variables).
</details>

<details>
<summary><strong>'export' is not recognized as an internal or external command</strong></summary>

`export` is a Mac/Linux-only command. On Windows, use `set VAR=value` (cmd) or `$env:VAR="value"` (PowerShell) instead.
</details>

---

## 🗺 Roadmap

- [ ] Multi-user support with Supabase Auth
- [ ] `.env` file support via `python-dotenv` for easier local credential management
- [ ] Recurring tasks
- [ ] Task reminders / notifications

---

## 📄 License

MIT — free to use, modify, and distribute.
