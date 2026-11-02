# dotfiles

My personal macOS dotfiles — zsh, git, and a handful of app configs, wired up with a single idempotent install script.

## What's inside

```
.
├── Brewfile                  # Homebrew taps, formulae, casks & editor extensions
├── install.sh                # symlinks everything into place (+ optional brew bundle)
├── shell/
│   ├── .zshrc                # Oh My Zsh, aliases, lazy nvm, PATH hygiene
│   ├── .zshenv               # env vars + PATH (loaded by every shell)
│   └── .zprofile             # login-shell setup (Homebrew, OrbStack)
├── git/
│   └── .gitconfig            # user, SSH commit signing, gh credential helper
├── config/                   # everything under ~/.config
│   ├── wezterm/wezterm.lua   # terminal: theme, keybinds, pane workflow
│   ├── zed/                  # Zed editor: settings.json + keymap.json
│   ├── skhd/skhdrc           # hotkey daemon (WezTerm pane focus)
│   └── iterm2/pane-title.zsh # pane title with branch / PR status
├── claude/                   # Claude Code: linked into ~/.claude
│   ├── CLAUDE.md             # global agent instructions
│   ├── settings.json         # hooks, plugins, marketplaces
│   ├── hooks/                # PreToolUse guards (commit format, CI polling, merges, heavy runs)
│   ├── agents/               # custom subagents
│   └── skills/               # slash-command skills (linked one by one)
└── bin/
    └── pr-status             # PR/CI/review status for agents (~/.local/bin)
```

Skills and agents are linked individually, so `~/.claude/skills` can also hold third-party and app-synced skills this repo doesn't track. `settings.local.json`, memory and session data stay local.

## Installation

1. **Install Apple's Command Line Tools** (prerequisite for git & Homebrew):

   ```bash
   xcode-select --install
   ```

2. **Clone the repo:**

   ```bash
   git clone https://github.com/ChiragAgg5k/dotfiles.git ~/Desktop/personal/dotfiles
   cd ~/Desktop/personal/dotfiles
   ```

3. **Run the installer.** It symlinks every tracked file into place (backing up
   anything it would overwrite to `~/.dotfiles-backup/<timestamp>/`), then offers
   to install the Brewfile packages:

   ```bash
   ./install.sh
   ```

   See exactly what it would do without changing anything:

   ```bash
   ./install.sh --dry-run
   ```

   Other flags: `--link` (symlink only), `--brew` (Brewfile only).

4. **Install Homebrew** (if you skipped it above and don't have it yet):

   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   brew bundle --file ~/Desktop/personal/dotfiles/Brewfile
   ```

## Post-install (one-time)

The shell config expects a few things the installer doesn't manage:

- **Oh My Zsh:**

  ```bash
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
  ```

- **zsh-autosuggestions** plugin (referenced by `.zshrc`):

  ```bash
  git clone https://github.com/zsh-users/zsh-autosuggestions \
    "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-autosuggestions"
  ```

  `zsh-syntax-highlighting` and `eza`/`bat` come from the Brewfile.

- **Secrets** live in `~/.zshrc.secrets` (sourced by `.zshrc`, never committed).
  Create it and add per-machine API keys / tokens:

  ```bash
  touch ~/.zshrc.secrets
  ```

- **PostHog MCP in Zed** (optional): the committed `config/zed/settings.json`
  ships a placeholder — replace `POSTHOG_AUTH_HEADER` with your own personal API
  key if you use that MCP server.

Then restart your shell: `exec zsh`.

## Notes

- The installer is idempotent — re-running it relinks anything that drifted and
  leaves correct links untouched.
- Symlinks point at wherever the repo is cloned, so after moving the clone re-run
  `./install.sh --link` to repoint them.
- Repos are laid out as `~/Desktop/appwrite/<org>/<repo>` for work and
  `~/Desktop/personal/<name>` for personal projects; `.zshrc` sets
  `SUPERPOWERD_HOME`/`SUPERPOWERD_WORKSPACE` to match.
- Some `.zshrc` entries reference personal tooling (`superpowerd`, `docker-use`);
  they're guarded so a missing tool won't break shell startup.
