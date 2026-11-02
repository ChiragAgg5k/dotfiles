export PATH="/Users/chiragaggarwal/.local/bin:$PATH"
# --------------------------- Oh-My-ZSH config ---------------------------
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="robbyrussell"
zstyle ':omz:update' mode disabled
DISABLE_UNTRACKED_FILES_DIRTY="true"
DISABLE_AUTO_TITLE="true"
plugins=(
    macos
    zsh-autosuggestions
    aliases
)
# Extend fpath BEFORE oh-my-zsh so its compinit picks these up (avoids a second compinit)
fpath=(/Users/chiragaggarwal/.docker/completions $fpath)
fpath=("/Users/chiragaggarwal/.local/share/zsh/site-functions" $fpath)
source $ZSH/oh-my-zsh.sh

# --------------------------- Constants ---------------------------
export SUPERPOWERD_HOME="/Users/chiragaggarwal/Local/superpowerd"
export SUPERPOWERD_WORKSPACE="/Users/chiragaggarwal/Local"
export CLAUDE_CODE_DISABLE_TERMINAL_TITLE=1
# Explicitly opt into allowing non-official Homebrew taps (silences tap-trust hints).
export HOMEBREW_NO_REQUIRE_TAP_TRUST=1

# --------------------------- Aliases ---------------------------
# Agents (Claude Code sets CLAUDECODE) need plain ls/cat output for scripting.
if [[ -z $CLAUDECODE ]]; then
  alias la="eza -la --no-user --header --icons -1 -l"
  alias ls="eza --no-user --header --icons -1 -l"
  alias cat='bat'
fi
alias pnpx="pnpm dlx"

# --------------------------- Tool-specific Interactive Configs ---------------------------
# bun completions
[ -s "$BUN_INSTALL/_bun" ] && source "$BUN_INSTALL/_bun"

# nvm — lazy load. The eager source costs ~900ms; stubs source it on first use.
# NVM_DIR is exported in .zshenv (needed by all shells).
# Put nvm's default node bin on PATH so npm globals (codex, claude, etc.) work without sourcing nvm.
# `command` prefixes bypass user aliases (ls→eza, cat→bat).
_nvm_resolve_default() {
  [ -f "$NVM_DIR/alias/default" ] || return
  local a=$(command cat "$NVM_DIR/alias/default")
  while [ -f "$NVM_DIR/alias/$a" ]; do a=$(command cat "$NVM_DIR/alias/$a"); done
  local bin
  if [[ "$a" == v* ]] && [ -d "$NVM_DIR/versions/node/$a/bin" ]; then
    bin="$NVM_DIR/versions/node/$a/bin"
  else
    bin=$(command ls -d "$NVM_DIR"/versions/node/v"${a#v}"*/bin 2>/dev/null | command sort -V | command tail -1)
  fi
  [ -d "$bin" ] && export PATH="$bin:$PATH"
}
_nvm_resolve_default
unset -f _nvm_resolve_default

_nvm_lazy_load() {
  unset -f nvm node npm npx 2>/dev/null
  [ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \. "/opt/homebrew/opt/nvm/nvm.sh"
  [ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm"
}
nvm()  { _nvm_lazy_load; nvm "$@"; }
node() { _nvm_lazy_load; node "$@"; }
npm()  { _nvm_lazy_load; npm "$@"; }
npx()  { _nvm_lazy_load; npx "$@"; }

# .local/bin is on PATH via .zshenv + the export at the top of this file.
export PATH="$HOME/.spin/bin:$PATH"

export PATH="/Users/chiragaggarwal/.antigravity/antigravity/bin:$PATH"

# superpowerd
[[ -f ~/.config/iterm2/pane-title.zsh ]] && source ~/.config/iterm2/pane-title.zsh
alias sp-rotate="/Users/chiragaggarwal/Local/superpowerd/rotation/rotate"
alias sp-monitor="/Users/chiragaggarwal/Local/superpowerd/rotation/monitor"
alias sp-update="/Users/chiragaggarwal/Local/superpowerd/rotation/update"
alias sp-dashboard="npx --yes tsx /Users/chiragaggarwal/Local/superpowerd/dashboard/server.ts"
alias sp-agent="/Users/chiragaggarwal/Local/superpowerd/sp-agent"
alias sp-reset="/Users/chiragaggarwal/Local/superpowerd/sp-reset"

# Secrets — sourced from a non-committed file so they don't sit in .zshrc
[ -f "$HOME/.zshrc.secrets" ] && source "$HOME/.zshrc.secrets"

# Warn if GITHUB_TOKEN is set — it overrides gh's keyring auth and is usually unintended.
# Why: gh prefers $GITHUB_TOKEN over the keyring, so a stale env var silently breaks `gh`.
if [ -n "$GITHUB_TOKEN" ]; then
  print -P "%F{yellow}⚠ GITHUB_TOKEN is set — this overrides gh's keyring auth. Run \`unset GITHUB_TOKEN\` if unintended.%f"
fi

# pnpm: PNPM_HOME + PATH are set in .zshenv (needed by all shells).

# Bootstrap go-task without installing globally (added for orchestrator repo)
alias task="go run github.com/go-task/task/v3/cmd/task@latest"

tilt() {
  if [[ "$1" == "up" ]]; then
    shift
    command tilt up --stream=false "$@"
  else
    command tilt "$@"
  fi
}

# Go binaries installed by `go install` (GOPATH defaults to ~/go; avoids forking `go env`)
export PATH="$PATH:${GOPATH:-$HOME/go}/bin"

# Keep PATH usable for tools that scan every entry, such as `kubectl plugin list`.
path_cleanup_existing() {
  local cleaned=()
  local entry
  for entry in ${(s/:/)PATH}; do
    [ -n "$entry" ] && [ -d "$entry" ] || continue
    if (( ${cleaned[(Ie)$entry]} == 0 )); then
      cleaned+=("$entry")
    fi
  done
  export PATH="${(j/:/)cleaned}"
}
path_cleanup_existing
unset -f path_cleanup_existing


# Docker Hub account switcher (https://github.com/ChiragAgg5k/docker-use)
eval "$(command docker-use init zsh)"

# zsh-syntax-highlighting MUST be sourced last, after all ZLE/widget setup
# (oh-my-zsh plugins, completions, docker-use init). Keep this at the very end.
source /opt/homebrew/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
