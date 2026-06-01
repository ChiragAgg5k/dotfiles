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
└── config/                   # everything under ~/.config
    ├── wezterm/wezterm.lua   # terminal: theme, keybinds, pane workflow
    ├── zed/                  # Zed editor: settings.json + keymap.json
    ├── skhd/skhdrc           # hotkey daemon (WezTerm pane focus)
    └── iterm2/pane-title.zsh # pane title with branch / PR status
```

## Installation

1. **Install Apple's Command Line Tools** (prerequisite for git & Homebrew):

   ```bash
   xcode-select --install
   ```

2. **Clone the repo:**

   ```bash
   git clone https://github.com/ChiragAgg5k/dotfiles.git ~/.dotfiles
   cd ~/.dotfiles
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
   brew bundle --file ~/.dotfiles/Brewfile
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
- Some `.zshrc` entries reference personal tooling (`superpowerd`, `docker-use`);
  they're guarded so a missing tool won't break shell startup.
