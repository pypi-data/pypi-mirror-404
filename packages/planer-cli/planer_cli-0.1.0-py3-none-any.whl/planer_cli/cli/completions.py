"""Shell completion generation for various shells."""

import click


@click.group()
def completions() -> None:
    """Generate shell completions for planer CLI.

    Generate completion scripts for your shell to enable tab completion
    for planer commands, options, and arguments.

    After generating the script, follow your shell's instructions to
    install it. Typical locations:

    \b
    Bash:
        ~/.bashrc or ~/.bash_completion

    \b
    Zsh:
        ~/.zshrc or a file in your $fpath

    \b
    Fish:
        ~/.config/fish/completions/planer.fish
    """
    pass


@completions.command()
def bash() -> None:
    """Generate Bash completion script.

    To enable completions, add this to your ~/.bashrc:

    \b
        eval "$(planer completions bash)"

    Or save to a file:

    \b
        planer completions bash > ~/.local/share/bash-completion/completions/planer
    """
    import os

    # Set the environment variable that Click uses to generate completions
    os.environ["_PLANER_COMPLETE"] = "bash_source"

    # Import the CLI to trigger completion generation
    from planer_cli.cli.main import cli

    # Click will output the completion script when this env var is set
    try:
        cli(standalone_mode=False)
    except SystemExit:
        pass


@completions.command()
def zsh() -> None:
    """Generate Zsh completion script.

    To enable completions, add this to your ~/.zshrc:

    \b
        eval "$(planer completions zsh)"

    Or save to a file in your fpath:

    \b
        planer completions zsh > ~/.zfunc/_planer

    Make sure ~/.zfunc is in your fpath before compinit is called.
    """
    import os

    os.environ["_PLANER_COMPLETE"] = "zsh_source"

    from planer_cli.cli.main import cli

    try:
        cli(standalone_mode=False)
    except SystemExit:
        pass


@completions.command()
def fish() -> None:
    """Generate Fish completion script.

    To enable completions, save to the Fish completions directory:

    \b
        planer completions fish > ~/.config/fish/completions/planer.fish

    Fish will automatically load completions from this directory.
    """
    import os

    os.environ["_PLANER_COMPLETE"] = "fish_source"

    from planer_cli.cli.main import cli

    try:
        cli(standalone_mode=False)
    except SystemExit:
        pass
