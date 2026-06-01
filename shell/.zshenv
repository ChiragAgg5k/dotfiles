export JAVA_HOME=$(/usr/libexec/java_home)
export BUN_INSTALL="$HOME/.bun"
export PNPM_HOME="$HOME/Library/pnpm"
export NVM_DIR="$HOME/.nvm"
export ANDROID_HOME="$HOME/Library/Android/sdk"

path_add() {
  [ -d "$1" ] && case ":$PATH:" in
    *":$1:"*) ;;
    *) export PATH="$PATH:$1" ;;
  esac
}

path_prepend() {
  [ -d "$1" ] && case ":$PATH:" in
    *":$1:"*) ;;
    *) export PATH="$1:$PATH" ;;
  esac
}

path_add "/opt/homebrew/opt/openjdk/bin"
path_add "/opt/homebrew/opt/openjdk@21/bin"

path_add "$HOME/development/flutter/bin"
path_add "/usr/local/mysql/bin"
path_add "$HOME/.local/bin"
path_add "$HOME/.rvm/bin"
path_add "/Library/TeX/texbin"
path_add "$HOME/.pub-cache/bin"
path_prepend "$BUN_INSTALL/bin"
path_add "$ANDROID_HOME/emulator"
path_add "$ANDROID_HOME/platform-tools"

case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) [ -d "$PNPM_HOME" ] && export PATH="$PNPM_HOME:$PATH" ;;
esac
[ -f "$HOME/.cargo/env" ] && . "$HOME/.cargo/env"

unset -f path_add path_prepend
