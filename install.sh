#!/usr/bin/env bash
#
# Dotfiles installer — symlinks tracked config files into place, then
# (optionally) installs Homebrew packages from the Brewfile.
#
# Usage:
#   ./install.sh            # symlink everything, then prompt for `brew bundle`
#   ./install.sh --link     # symlink only, skip Homebrew
#   ./install.sh --brew     # run `brew bundle` only, skip symlinking
#   ./install.sh --dry-run  # print what would happen, change nothing
#
# Env overrides (handy for testing):
#   DOTFILES_DIR     repo location          (default: this script's directory)
#   DOTFILES_TARGET  where links are placed  (default: $HOME)
#
set -euo pipefail

DOTFILES_DIR="${DOTFILES_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
TARGET="${DOTFILES_TARGET:-$HOME}"

DO_LINK=true
DO_BREW=ask
DRY_RUN=false
for arg in "$@"; do
  case "$arg" in
    --link)    DO_BREW=false ;;
    --brew)    DO_LINK=false; DO_BREW=true ;;
    --dry-run) DRY_RUN=true ;;
    -h|--help) sed -n '3,14p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

# Map of repo-relative source -> target-relative destination.
LINKS=(
  "shell/.zshrc:.zshrc"
  "shell/.zshenv:.zshenv"
  "shell/.zprofile:.zprofile"
  "git/.gitconfig:.gitconfig"
  "config/wezterm/wezterm.lua:.config/wezterm/wezterm.lua"
  "config/zed/settings.json:.config/zed/settings.json"
  "config/zed/keymap.json:.config/zed/keymap.json"
  "config/skhd/skhdrc:.config/skhd/skhdrc"
  "config/iterm2/pane-title.zsh:.config/iterm2/pane-title.zsh"
  "claude/CLAUDE.md:.claude/CLAUDE.md"
  "claude/settings.json:.claude/settings.json"
  "bin/pr-status:.local/bin/pr-status"
)

# Claude Code hooks, agents and skills are linked one by one so ~/.claude/skills can also
# hold third-party skills and app-synced ones that this repo doesn't track.
for path in "$DOTFILES_DIR"/claude/hooks/* "$DOTFILES_DIR"/claude/agents/* "$DOTFILES_DIR"/claude/skills/*; do
  [ -e "$path" ] && LINKS+=("${path#"$DOTFILES_DIR"/}:.${path#"$DOTFILES_DIR"/}")
done

info()  { printf '\033[34m•\033[0m %s\n' "$1"; }
ok()    { printf '\033[32m✓\033[0m %s\n' "$1"; }
warn()  { printf '\033[33m!\033[0m %s\n' "$1"; }
run()   { if [ "$DRY_RUN" = true ]; then echo "  would: $*"; else "$@"; fi; }

link_files() {
  local backup_dir="$TARGET/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)"
  info "Linking dotfiles from $DOTFILES_DIR into $TARGET"
  for pair in "${LINKS[@]}"; do
    local src="$DOTFILES_DIR/${pair%%:*}"
    local dest="$TARGET/${pair##*:}"
    if [ ! -e "$src" ]; then warn "missing source, skipping: $src"; continue; fi

    # Already correctly linked? Nothing to do (idempotent).
    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
      ok "already linked: ${pair##*:}"
      continue
    fi

    run mkdir -p "$(dirname "$dest")"

    # Back up an existing real file or wrong symlink before replacing it.
    if [ -e "$dest" ] || [ -L "$dest" ]; then
      run mkdir -p "$backup_dir/$(dirname "${pair##*:}")"
      run mv "$dest" "$backup_dir/${pair##*:}"
      warn "backed up existing ${pair##*:} -> $backup_dir/${pair##*:}"
    fi

    run ln -s "$src" "$dest"
    ok "linked ${pair##*:}"
  done
}

brew_bundle() {
  if ! command -v brew >/dev/null 2>&1; then
    warn "Homebrew not found. Install it first:"
    echo '    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    return
  fi
  info "Installing packages from Brewfile (this can take a while)…"
  run brew bundle --file "$DOTFILES_DIR/Brewfile"
  ok "Homebrew packages installed"
}

[ "$DO_LINK" = true ] && link_files

if [ "$DO_BREW" = ask ] && [ "$DRY_RUN" = false ]; then
  read -r -p "Run \`brew bundle\` to install packages now? [y/N] " reply
  [[ "$reply" =~ ^[Yy]$ ]] && DO_BREW=true || DO_BREW=false
fi
[ "$DO_BREW" = true ] && brew_bundle

echo
ok "Done."
cat <<'NEXT'

Next steps (one-time, not handled by this script):
  • Install Oh My Zsh:
      sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
  • Install the zsh-autosuggestions plugin into Oh My Zsh's custom dir:
      git clone https://github.com/zsh-users/zsh-autosuggestions \
        "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-autosuggestions"
  • Copy secrets template and fill it in (sourced by .zshrc, never committed):
      touch ~/.zshrc.secrets   # add per-machine API keys / tokens here
  • In Zed, set POSTHOG_AUTH_HEADER in config/zed/settings.json if you use the PostHog MCP server.
  • Restart your shell:  exec zsh
NEXT
