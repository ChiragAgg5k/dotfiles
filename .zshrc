eval "$(pyenv init --path)" # pyenv setup for default interpreter
alias python=python3 # alias python3 to python

# ---------------------------Oh-My-ZSH config ---------------------------
export ZSH="$HOME/.oh-my-zsh" # Path to your oh-my-zsh installation.
ZSH_THEME="robbyrussell" # zsh theme
zstyle ':omz:update' mode disabled # update automatically without asking
DISABLE_UNTRACKED_FILES_DIRTY="true" # this makes repository status check much,much faster
plugins=(
    macos
    zsh-autosuggestions
    aliases
    zsh-syntax-highlighting
)

source $ZSH/oh-my-zsh.sh
# ------------------------------------------------------------------------

# -----------------------Exporting Paths----------------------------------
export PATH=$PATH:/opt/homebrew/bin/pyenv # Pyenv
export PATH=$PATH:/Users/chiragagg5k/development/flutter/bin # Flutter
export PATH=${PATH}:/usr/local/mysql/bin/ # Mysql
export PATH=$PATH:/Users/chiragagg5k/.local/bin # Lunar Vim
export PATH=$PATH:/Users/chiragagg5k/.rvm/bin # Ruby enVironment Manager
export PATH=$PATH:/opt/homebrew/Cellar/ascii-image-converter/1.13.1-next/bin # ASCII Image Converter
export PATH=$PATH:/opt/homebrew/anaconda3/bin # Anaconda
export PATH=$PATH:/Library/TeX/texbin # Latex Stuff
export JAVA_HOME=$(/usr/libexec/java_home) # Java Home
export PATH="$PATH":"$HOME/.pub-cache/bin" # Flutter Fire
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH" # OpenJDK
export JAVA_HOME=$(/usr/libexec/java_home) # Java Home
export PATH="/opt/homebrew/opt/swift/bin:$PATH" # Swift
export PNPM_HOME="/Users/chiragagg5k/Library/pnpm" # pnpm
# -------------------------------------------------------------------------

alias la="exa -la --no-user --header --icons -1 -l" # exa command to show hidden files as well
alias ls="exa --no-user --header --icons -1 -l" # exa command aliased to ls
alias cat='bat' # using cat replacement, bat

# The next line updates PATH for the Google Cloud SDK.
if [ -f '/Users/chiragagg5k/google-cloud-sdk/path.zsh.inc' ]; then . '/Users/chiragagg5k/google-cloud-sdk/path.zsh.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f '/Users/chiragagg5k/google-cloud-sdk/completion.zsh.inc' ]; then . '/Users/chiragagg5k/google-cloud-sdk/completion.zsh.inc'; fi

# pnpm
alias pnpx="pnpm dlx"
case ":$PATH:" in
  *":$PNPM_HOME:"*) ;;
  *) export PATH="$PNPM_HOME:$PATH" ;;
esac
# pnpm end

# Silly greeting 
cyan='\033[0;36m'
echo "${cyan}Hello There!\n"