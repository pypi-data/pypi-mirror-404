"""Authentication helper functions for Lookout CLI."""

from typing import List

import bcrypt
import click

from lookout_config.types import AuthCredential, LookoutConfig


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The plain text password to hash

    Returns:
        The bcrypt-hashed password as a UTF-8 string

    Raises:
        ValueError: If password is empty or None
    """
    if not password:
        raise ValueError("Password cannot be empty")

    try:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to hash password: {e}") from e


def configure_auth_prompt(config_current: LookoutConfig) -> list[AuthCredential]:
    """Configure authentication settings interactively.

    Prompts the user to configure authentication credentials, allowing them to:
    - Skip authentication setup
    - Keep existing credentials
    - Add new credentials
    - Use default credentials if none are configured

    Args:
        config_current: The current Lookout configuration

    Returns:
        A list of AuthCredential objects representing the configured credentials
    """

    setup_auth = click.prompt(
        "Do you want to set up authentication?",
        default="y",
        type=click.Choice(["y", "n"]),
    )

    if setup_auth == "n":
        return config_current.proxy.auth_credentials

    credentials: List[AuthCredential] = []

    # Handle existing credentials
    if config_current.proxy.auth_credentials:
        click.echo("Existing credentials found. You can update them or add new ones.")
        for i, cred in enumerate(config_current.proxy.auth_credentials):
            click.echo(f"  {i+1}. {cred.username}")

        use_existing = click.prompt(
            "Keep existing credentials?",
            default="y",
            type=click.Choice(["y", "n"]),
        )
        if use_existing == "y":
            credentials = list(config_current.proxy.auth_credentials)

    # Add new credentials
    while True:
        add_more = click.prompt(
            "Add a user credential?",
            default="y" if not credentials else "n",
            type=click.Choice(["y", "n"]),
        )

        if add_more == "n":
            break

        username = click.prompt("Username", default="operator")
        password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

        try:
            hashed_password = hash_password(password)
            credentials.append(AuthCredential(username=username, hashed_password=hashed_password))
            click.echo(f"Added user: {username}")
        except ValueError as e:
            click.echo(click.style(f"Error: {e}", fg="red"))
            continue

    return credentials
