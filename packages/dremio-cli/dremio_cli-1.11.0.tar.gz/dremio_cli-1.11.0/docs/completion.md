# Shell Completion

Generate shell completion scripts for Bash, Zsh, and Fish.

## Usage

```bash
dremio completion [bash|zsh|fish]
```

## Installation

### Bash

Add this to your `~/.bashrc`:

```bash
eval "$(_DREMIO_COMPLETE=bash_source dremio)"
```

### Zsh

Add this to your `~/.zshrc`:

```bash
eval "$(_DREMIO_COMPLETE=zsh_source dremio)"
```

### Fish

Add this to your `~/.config/fish/config.fish`:

```fish
eval (env _DREMIO_COMPLETE=fish_source dremio)
```

After adding the line, restart your shell or source the config file to enable tab completion.
