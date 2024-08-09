import logging
import sys

import click
from click import Context
from git import InvalidGitRepositoryError, NoSuchPathError

import aicommit
from aicommit.config_manager import ConfigManager
from aicommit.exceptions import ConfigKeyError, GitNoStagedChanges, KeyNotFound
from aicommit.hook import AICommitHook
from aicommit.message_generator import MessageGenerator
from aicommit.utils import common_options

logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(filename)s::%(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.WARNING,
)


@click.group(
    name="aicommit",
    help="AI-Powered Git Commit Message Generator",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.pass_context
@common_options
@click.version_option(
    aicommit.__version__,
    "--version",
    "-v",
    prog_name="aicommit",
    message="%(prog)s: %(version)s",
)
def cli(ctx: Context, debug, local):
    """AICommit CLI"""
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.debug(f"Running with debug={debug}, local={local}")

    ctx.obj["debug"] = debug
    ctx.obj["local"] = local
    ctx.obj["config_manager"]: ConfigManager = None


@cli.group(name="config")
@click.pass_context
@common_options
def config(ctx, debug, local):
    """Manage aicommit configuration."""
    logger.debug(f"Config manage, local={local}")
    if not ctx.obj["config_manager"]:
        ctx.obj["config_manager"] = ConfigManager(ctx.obj["local"])


config: click.Group  # type hints for IDE


@config.command("set", help="Set a configuration value.")
@click.argument("key")
@click.argument("value")
@click.pass_context
@common_options
def config_set(ctx: Context, key, value, debug, local):
    """Set a configuration value."""
    try:
        ctx.obj["config_manager"].set(key, value)
        click.echo(
            f"[AICommit] Set {click.style(key, fg='green')} to {click.style(value, fg='green')}."
        )
    except ConfigKeyError as e:
        click.echo(f"[AICommit] Error: {e!s}")


@config.command("get")
@click.argument("key")
@click.pass_context
@common_options
def config_get(ctx, key, debug, local):
    """Get a configuration value."""
    try:
        value = ctx.obj["config_manager"].get(key)
        click.echo(f"{key}: {value}")
    except ValueError as e:
        click.echo(f"Error: {e!s}")
    except ConfigKeyError as e:
        click.echo(str(e))


@config.command("list")
@click.pass_context
@common_options
def config_list(ctx: Context, debug, local):
    """List all configuration values."""
    click.echo(
        click.style("Current configuration:\n", fg="green") + ctx.obj["config_manager"].list()
    )


@config.command("reset")
@click.pass_context
@common_options
def reset(ctx: Context, debug, local):
    """Reset configuration to default values."""
    ctx.obj["config_manager"].reset()
    click.echo("Configuration reset to default values")


@config.command(name="keys")
@click.pass_context
@common_options
def config_keys(ctx, debug, local):
    cfg_manager: ConfigManager = ctx.obj["config_manager"]
    keys = cfg_manager.list_keys()
    click.echo(click.style("Supported keys:\n", fg="green") + keys)


@config.command("path")
@click.pass_context
@common_options
def config_path(ctx: Context, debug, local):
    """Get the path to the configuration file."""
    click.echo(
        click.style("Current configuration path:\n", fg="green")
        + ctx.obj["config_manager"].current_config_path.as_posix()
    )


@cli.group("hook", help="Manage AICommit prepare-commit-msg hook.")
@common_options
@click.pass_context
def hook(ctx, debug, local):
    pass


hook: click.Group  # type hints for IDE


@hook.command("install", help="Install AICommit prepare-commit-msg hook to current repository.")
@click.option(
    "--force/--no-force",
    "-f/-nf",
    default=False,
    help="Force installation or not.",
    show_default=True,
)
@common_options
@click.pass_context
def install_hook(ctx, debug, local, force=False):
    """Install AICommit prepare-commit-msg hook."""
    try:
        comet_hook = AICommitHook()
        if comet_hook.is_hook_installed() and not force:
            click.echo(
                "AICommit prepare-commit-msg hook is already installed, use --force to force installation."
            )
            return
        comet_hook.install_hook()
        click.echo("AICommit prepare-commit-msg hook has been installed successfully.")
    except InvalidGitRepositoryError as e:
        click.echo(f"Error: {e!s}")
    except Exception as e:
        click.echo(f"An error occurred while installing the hook: {e!s}")


@hook.command("uninstall", help="Uninstall AICommit prepare-commit-msg hook from current repository.")
@common_options
@click.pass_context
def uninstall_hook(ctx, debug, local, **kwargs):
    """Uninstall AICommit prepare-commit-msg hook."""
    try:
        comet_hook = AICommitHook()
        comet_hook.uninstall_hook()
    except (InvalidGitRepositoryError, NoSuchPathError) as e:
        click.echo(f"Error: {e!s}")
    except Exception as e:
        click.echo(f"An error occurred while uninstalling the hook: {e!s}")


@hook.command("status")
def hook_status():
    """Check if AICommit prepare-commit-msg hook is installed."""
    try:
        comet_hook = AICommitHook()
        if comet_hook.is_hook_installed():
            click.echo("AICommit prepare-commit-msg hook is installed.")
        else:
            click.echo(
                f"AICommit prepare-commit-msg hook is {click.style('not', fg='yellow')} installed."
            )
    except InvalidGitRepositoryError as e:
        click.echo(f"Error: {e!s}")
    except Exception as e:
        click.echo(f"An error occurred while checking the hook status: {e!s}")


@cli.group("generate", help="Generate a commit message based on `git diff --staged`.")
@click.pass_context
@common_options
def generate(ctx, debug, local):
    ctx.obj["config_manager"] = ConfigManager(ctx.obj["local"])


generate: click.Group  # type hints for IDE


@generate.command("commit")
# @click.option("--rich", is_flag=True, default=False, help="Generate rich commit message")
@common_options
@click.pass_context
def generate_commit(ctx, debug, local, rich=False, **kwargs):
    """Generate a commit message based on git diff"""
    click.echo(
        click.style(
            "🤖 Hang tight! I'm having a chat with the AI to craft your commit message...",
            fg="green",
        )
    )
    config_manager = ctx.obj["config_manager"]
    message_generator = MessageGenerator(config_manager)
    retry = True
    commit_msg = None
    while retry:
        try:
            commit_msg = message_generator.generate_commit_message(rich)
        except KeyNotFound as e:
            click.echo(f"Error: {e!s}, please check your configuration.")
            raise click.Abort() from None
        except GitNoStagedChanges as e:
            click.echo(str(e))
            raise click.Abort() from None

        if commit_msg is None:
            click.echo(click.style("No commit message generated.", fg="magenta"))
            return

        click.echo(click.style("Generated commit message:", fg="green"))
        click.echo(commit_msg)

        if sys.stdin.isatty():
            # Interactive mode will ask for confirmation
            char = click.prompt(
                click.style(
                    "Do you want to use this commit message? y: yes, n: no, r: retry.", fg="green"
                ),
                default="y",
                type=click.Choice(["y", "n", "r"]),
            )
        else:
            click.echo(
                click.style(
                    "Non-interactive mode detected, using the generated commit message directly.",
                    fg="yellow",
                )
            )
            char = "y"

        if char == "n":
            click.echo(click.style("Commit message discarded.", fg="yellow"))
            return
        elif char == "y":
            retry = False
        logger.debug(f"Input: {char}")
        if char == "n":
            click.echo(click.style("Commit message discarded.", fg="yellow"))
            return
        elif char == "y":
            retry = False

    message_generator.repo.index.commit(commit_msg)
    click.echo(click.style("Commit message saved.", fg="green"))


@click.command()
@click.pass_context
def generate_prmsg(ctx, debug, local):
    """Generate a pull request message based on changes compared to master"""
    config_manager = ctx.obj["config_manager"]
    message_generator = MessageGenerator(config_manager)

    pr_msg = message_generator.generate_pr_message()

    click.echo("Generated pull request message:")
    click.echo(pr_msg)

    if click.confirm("Do you want to use this pull request message?"):
        # Here you could integrate with your Git hosting platform's API
        # to create a pull request with this message
        click.echo(
            "Pull request message saved. You can now use it to create a PR on your Git hosting platform."
        )
    else:
        click.echo("Pull request message discarded.")


if __name__ == "__main__":
    cli()
