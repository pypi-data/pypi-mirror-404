Shell Completion
================

Tab completion for bash, zsh, and fish shells.


Quick Install
-------------

Use ``--install-shell-completions`` to install tab completions::

    # Auto-detect shell from $SHELL
    myapp --install-shell-completions

    # Or specify shell explicitly
    myapp --install-shell-completions zsh
    myapp --install-shell-completions bash
    myapp --install-shell-completions fish

This installs completions and prints activation instructions.

.. note::

   Shell completions only work when the script is run as a **named command**
   (e.g., ``myapp``), not when invoked via ``python script.py``.

   To make this work:

   1. Install your package: ``pip install -e .``
   2. Define an entry point in ``pyproject.toml``::

        [project.scripts]
        myapp = "mypackage.cli:main"

   3. Now ``myapp --install-shell-completions`` works, and tab completion
      triggers when you type ``myapp <TAB>``.


Programmatic Installation
-------------------------

You can also install completions programmatically::

    from vidhi.cli_completion import install_completion
    from vidhi.flat_dataclass import create_flat_dataclass

    FlatConfig = create_flat_dataclass(AppConfig)

    # Auto-install to shell config
    install_completion(FlatConfig, "myapp")

    # Or specify shell explicitly
    install_completion(FlatConfig, "myapp", shell="zsh")


Generating Scripts
------------------

Generate completion scripts without installing::

    from vidhi.cli_completion import generate_completion_script

    # Get script as string
    script = generate_completion_script(FlatConfig, "myapp", "bash")

    # Print to stdout
    print(script)


Manual Setup
------------

If you prefer manual installation:

**Bash** - Add to ``~/.bashrc``::

    eval "$(myapp --print-completion bash)"

Or save to a file::

    myapp --print-completion bash > ~/.local/share/bash-completion/completions/myapp
    source ~/.bashrc

**Zsh** - Add to ``~/.zshrc``::

    eval "$(myapp --print-completion zsh)"

Or save to completions directory::

    myapp --print-completion zsh > ~/.zsh/completions/_myapp
    # Add to fpath in .zshrc: fpath=(~/.zsh/completions $fpath)
    autoload -Uz compinit && compinit

**Fish** - Save to completions directory::

    myapp --print-completion fish > ~/.config/fish/completions/myapp.fish

Fish automatically loads completions from this directory.


What Gets Completed
-------------------

Vidhi shell completions provide:

- All ``--option`` names
- Boolean values (``true``/``false``) for boolean arguments
- Enum/choice values for type selectors and choice fields
- File paths for relevant arguments
