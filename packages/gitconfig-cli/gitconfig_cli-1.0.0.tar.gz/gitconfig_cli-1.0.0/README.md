Here’s a **production-quality `README.md`** you can drop in as-is.
Clear, honest, PyPI-friendly, and actually useful. No marketing fluff.

---

````md
# gitconfig-cli

A **cross-platform CLI tool** to manage **Git + SSH multi-account setups** without pain.

If you use:
- multiple GitHub/GitLab accounts (work + personal),
- multiple SSH keys,
- different Git identities per repository,

this tool fixes the usual SSH chaos **once and for all**.

---

## ✨ Features

- ✅ Multi-account SSH support (work, personal, client, etc.)
- ✅ Multiple SSH keys per machine
  - `ed25519` (default, recommended)
  - `rsa` (legacy / enterprise opt-in)
- ✅ Automatic `~/.ssh/config` management with host aliases
- ✅ Per-repository Git identity switching
- ✅ SSH authentication testing (with verbose debug mode)
- ✅ SSH environment diagnostics (`doctor`)
- ✅ Configuration export for backup
- ✅ No destructive global Git changes
- ✅ Linux, macOS, and Windows support

---

## 🚀 Installation

### Using pip
```bash
pip install gitconfig-cli
````

### Recommended (isolated install)

```bash
pipx install gitconfig-cli
```

---

## 🧠 How it works (important)

Instead of fighting SSH, this tool:

* creates **named SSH keys**
* assigns **SSH host aliases** (e.g. `github-work`)
* pins the correct key per repository

You clone using aliases like:

```bash
git clone git@github-work:org/repo.git
```

No more “wrong account” surprises.

---

## 📦 Basic Usage

### Add an SSH account

```bash
gitconfig add \
  --provider github \
  --account work \
  --email work@company.com
```

This will:

* generate an SSH key
* update `~/.ssh/config`
* register the account locally

---

### List accounts

```bash
gitconfig list
```

Example output:

```
- work → github (ed25519) [git@github-work]
- personal → github (ed25519) [git@github-personal]
```

---

### Use an account in a repo

```bash
cd some-repo
gitconfig use work
```

This sets **only for that repo**:

* `user.email`
* `core.sshCommand` (forces correct SSH key)

Global Git config remains untouched.

---

### Test SSH authentication

```bash
gitconfig test work
```

Verbose SSH debugging:

```bash
gitconfig test work --verbose
```

---

### Run SSH diagnostics

```bash
gitconfig doctor
```

Checks:

* `ssh` availability
* `~/.ssh` permissions
* `ssh-agent` status
* common misconfigurations

---

### Export configuration (backup)

```bash
gitconfig export
```

To file:

```bash
gitconfig export --output backup.json
```

---

## 🔐 About `ssh-rsa`

* `ssh-rsa` is **deprecated** and disabled by default in modern OpenSSH.
* Some enterprise servers still require it.

You can opt-in safely:

```bash
gitconfig add --provider github --account legacy --email x@y.com --key-type rsa
```

⚠️ RSA is **never enabled globally**, only per host alias.

---

## 🗂 Configuration Location

Internal config is stored at:

```text
~/.config/gitconfig-cli/config.json
```

SSH keys and config:

```text
~/.ssh/
```

---

## ❌ What this tool does NOT do

* ❌ Upload SSH keys to GitHub/GitLab automatically
* ❌ Modify your global Git identity without asking
* ❌ Hide what it’s doing behind magic

Everything is explicit and inspectable.

---

## 🛠 Requirements

* Python 3.8+
* Git
* OpenSSH

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

## 🧭 Roadmap

* JSON output for CI / scripting
* `gitconfig doctor --fix`
* Account import / restore
* Shell completion

---

## 💬 Feedback

Issues and PRs are welcome.
This tool exists to kill SSH confusion — permanently.
