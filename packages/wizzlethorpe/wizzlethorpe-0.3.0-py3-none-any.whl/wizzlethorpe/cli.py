"""Wizzlethorpe CLI."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from wizzlethorpe.client import AuthenticationError, WizzlethorpeClient, WizzlethorpeError
from wizzlethorpe.config import (
    get_config_value,
    list_config,
    set_config_value,
    unset_config_value,
)


def get_client(**kwargs) -> WizzlethorpeClient:
    """Create client (reads WIZZLETHORPE_BASE_URL and OPENAI_API_KEY from env)."""
    return WizzlethorpeClient(**kwargs)


@click.group()
@click.version_option()
def main():
    """Wizzlethorpe Labs CLI - TTRPG tools."""


# === Auth Commands ===


@main.command()
def login():
    """Link your Patreon account via browser."""
    client = get_client()

    # Check if already logged in
    user = client.me()
    if user:
        click.echo(f"Already logged in as {user.name} ({user.tier_name})")
        if not click.confirm("Login again?"):
            return

    try:
        link = client.link()
        # Include device name in URL for proper device tracking
        link_url = f"{link.link_url}&device=CLI"
        click.echo(f"\nGo to: {client.base_url}{link_url}")
        click.echo(f"Or visit {client.base_url}/link?device=CLI and enter: {click.style(link.code, bold=True, fg='cyan')}\n")
        click.echo("Waiting for authorization...")

        user = client.poll_link(link.code)
        click.echo(f"\n{click.style('Success!', fg='green')} Logged in as {user.name}")
        click.echo(f"Tier: {user.tier_name}")

    except AuthenticationError as e:
        click.echo(f"Login failed: {e}", err=True)
        sys.exit(1)


@main.command()
def logout():
    """Clear saved authentication."""
    client = get_client()
    client.logout()
    click.echo("Logged out.")


@main.command()
def whoami():
    """Show current user info."""
    client = get_client()
    user = client.me()
    if user:
        click.echo(f"Name: {user.name}")
        click.echo(f"Email: {user.email}")
        click.echo(f"Tier: {user.tier_name} (${user.tier_cents / 100:.2f}/mo)")
    else:
        click.echo("Not logged in. Run 'wizzlethorpe login' to authenticate.")


# === Config Management ===


@main.group()
def config():
    """Manage configuration settings."""


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set a configuration value.

    Examples:
      wzl config set api_key sk-...
      wzl config set base_url https://example.com
    """
    set_config_value(key, value)
    click.echo(f"Set {key} = {value}")


@config.command("get")
@click.argument("key")
def config_get(key: str):
    """Get a configuration value."""
    value = get_config_value(key)
    if value:
        click.echo(f"{key} = {value}")
    else:
        click.echo(f"{key} not set", err=True)
        sys.exit(1)


@config.command("unset")
@click.argument("key")
def config_unset(key: str):
    """Remove a configuration value."""
    unset_config_value(key)
    click.echo(f"Removed {key}")


@config.command("list")
def config_list():
    """List all configuration values."""
    cfg = list_config()
    if not cfg:
        click.echo("No configuration set.")
        return

    for key, value in sorted(cfg.items()):
        # Mask sensitive values
        if "key" in key.lower() or "token" in key.lower():
            masked = value[:8] + "..." if len(value) > 8 else "***"
            click.echo(f"{key} = {masked}")
        else:
            click.echo(f"{key} = {value}")


# === Cocktails Product ===


@main.group()
def cocktails():
    """Bixby's Cocktails - magical cocktail recipes."""


@cocktails.command("list")
@click.option("--liquor", "-l", help="Filter by base liquor")
@click.option("--ingredient", "-i", help="Filter by ingredient")
def cocktails_list(liquor: str | None, ingredient: str | None):
    """List all cocktails."""
    client = get_client()
    items = client.cocktails.list()

    if liquor:
        liquor_lower = liquor.lower()
        liquors_map = {liq.id: liq for liq in client.cocktails.liquors()}
        items = [c for c in items if liquors_map.get(c.liquor_id, "").name.lower() == liquor_lower]

    if ingredient:
        ing_lower = ingredient.lower()
        ings = {i.id: i for i in client.cocktails.ingredients()}
        items = [c for c in items if ings.get(c.ingredient_id, "").name.lower() == ing_lower]

    for c in items:
        click.echo(f"{click.style(c.name, bold=True)}: {c.description[:60]}...")


@cocktails.command("get")
@click.argument("name")
def cocktails_get(name: str):
    """Get details for a specific cocktail."""
    client = get_client()
    cocktail = client.cocktails.get(name)

    if not cocktail:
        click.echo(f"Cocktail '{name}' not found.", err=True)
        sys.exit(1)

    # Get liquor and ingredient names
    liquors_map = {liq.id: liq for liq in client.cocktails.liquors()}
    ings = {i.id: i for i in client.cocktails.ingredients()}

    liquor = liquors_map.get(cocktail.liquor_id)
    ing = ings.get(cocktail.ingredient_id)

    click.echo(f"{click.style(cocktail.name, bold=True)}")
    click.echo(f"Base: {liquor.name if liquor else 'Unknown'}")
    click.echo(f"Ingredient: {ing.name if ing else 'Unknown'}")
    click.echo(f"\n\"{cocktail.description}\"")
    click.echo(f"\nAppearance: {cocktail.appearance}")
    click.echo(f"\nEffects (1d4):")
    click.echo(f"  1: {cocktail.effects.roll1}")
    click.echo(f"  2: {cocktail.effects.roll2}")
    click.echo(f"  3: {cocktail.effects.roll3}")
    click.echo(f"  4: {cocktail.effects.roll4}")


@cocktails.command("ingredients")
@click.option("--environment", "-e", help="Filter by environment")
def cocktails_ingredients(environment: str | None):
    """List magical ingredients."""
    client = get_client()
    items = client.cocktails.ingredients(environment)

    for i in items:
        envs = ", ".join(i.environments[:3])
        click.echo(f"{click.style(i.name, bold=True)} ({envs}): {i.description[:50]}...")


@cocktails.command("liquors")
def cocktails_liquors():
    """List base liquors."""
    client = get_client()
    for liq in client.cocktails.liquors():
        click.echo(f"{click.style(liq.name, bold=True)}: {liq.description}")


@cocktails.command("garnishes")
def cocktails_garnishes():
    """List garnishes."""
    client = get_client()
    for g in client.cocktails.garnishes():
        click.echo(f"{click.style(g.name, bold=True)}: {g.description}")


# === Quickbrush Product ===


@main.group()
def quickbrush():
    """Quickbrush - AI image generation for TTRPGs."""


def _quickbrush_generate(
    image_type: str,
    prompt: str,
    context: str | None,
    quality: str,
    aspect_ratio: str,
    reference: tuple[str, ...],
    output: str | None,
):
    """Shared generation logic."""
    client = get_client()

    refs = [Path(r) for r in reference] if reference else None

    click.echo(f"Generating {image_type}...")

    try:
        image = client.quickbrush.generate(
            image_type=image_type,  # type: ignore
            prompt=prompt,
            context=context,
            quality=quality,  # type: ignore
            aspect_ratio=aspect_ratio,  # type: ignore
            reference_images=refs,
        )

        # Default output path
        if not output:
            output = f"{image_type}.webp"

        path = image.save(output)
        click.echo(f"{click.style('Done!', fg='green')} Saved to {path}")

        if image.revised_prompt:
            click.echo(f"Revised prompt: {image.revised_prompt[:100]}...")

    except AuthenticationError:
        click.echo("Authentication required. Set OPENAI_API_KEY or run 'wizzlethorpe login'.", err=True)
        sys.exit(1)
    except WizzlethorpeError as e:
        click.echo(f"Generation failed: {e}", err=True)
        sys.exit(1)


# Common options for quickbrush commands
_qb_options = [
    click.option("--context", "-c", help="Context for generation"),
    click.option("--quality", "-q", default="auto", type=click.Choice(["low", "medium", "high", "auto"])),
    click.option("--aspect-ratio", "-a", default="square", type=click.Choice(["square", "landscape", "portrait", "wide"])),
    click.option("--reference", "-r", multiple=True, type=click.Path(exists=True), help="Reference image (up to 4)"),
    click.option("--output", "-o", help="Output file path"),
]


def add_options(options):
    """Decorator to add multiple options."""
    def decorator(f):
        for opt in reversed(options):
            f = opt(f)
        return f
    return decorator


@quickbrush.command("character")
@click.argument("prompt")
@add_options(_qb_options)
def qb_character(prompt, **kwargs):
    """Generate a character image."""
    _quickbrush_generate("character", prompt, **kwargs)


@quickbrush.command("scene")
@click.argument("prompt")
@add_options(_qb_options)
def qb_scene(prompt, **kwargs):
    """Generate a scene image."""
    _quickbrush_generate("scene", prompt, **kwargs)


@quickbrush.command("creature")
@click.argument("prompt")
@add_options(_qb_options)
def qb_creature(prompt, **kwargs):
    """Generate a creature image."""
    _quickbrush_generate("creature", prompt, **kwargs)


@quickbrush.command("item")
@click.argument("prompt")
@add_options(_qb_options)
def qb_item(prompt, **kwargs):
    """Generate an item image."""
    _quickbrush_generate("item", prompt, **kwargs)


# === Languages Product ===


@main.group()
def languages():
    """Languages - fantasy language translation."""


@languages.command("list")
def languages_list():
    """List available languages."""
    client = get_client()
    for lang in client.languages.list():
        click.echo(f"{click.style(lang.id, bold=True)}: {lang.name}")
        click.echo(f"  {lang.description[:80]}...")


@languages.command("translate")
@click.argument("text")
@click.option("--language", "-l", default="elvish", help="Target language (e.g., elvish, dwarvish)")
@click.option("--no-back-translation", is_flag=True, help="Skip back-translation")
def languages_translate(text: str, language: str, no_back_translation: bool):
    """Translate English text into a fantasy language.

    Examples:
      wzl languages translate "The warrior fights bravely."
      wzl languages translate "Hello friend" -l dwarvish
    """
    client = get_client()

    try:
        result = client.languages.translate(
            text,
            language,
            include_back_translation=not no_back_translation,
        )

        click.echo(f"\n{click.style('Source:', fg='cyan')} {result.source}")
        click.echo(f"{click.style(result.language_name + ':', fg='green')} {result.target}")

        if result.back_translation:
            click.echo(f"{click.style('Back-translation:', fg='yellow')} {result.back_translation}")

    except WizzlethorpeError as e:
        click.echo(f"Translation failed: {e}", err=True)
        sys.exit(1)


# Convenience alias for translate at top level
@main.command("translate")
@click.argument("text")
@click.option("--language", "-l", default="elvish", help="Target language (e.g., elvish, dwarvish)")
def translate_shortcut(text: str, language: str):
    """Translate English text into a fantasy language (shortcut).

    Examples:
      wzl translate "The warrior fights."
      wzl translate "Hello friend" -l dwarvish
    """
    client = get_client()

    try:
        result = client.languages.translate(text, language)

        click.echo(f"\n{click.style('Source:', fg='cyan')} {result.source}")
        click.echo(f"{click.style(result.language_name + ':', fg='green')} {result.target}")

        if result.back_translation:
            click.echo(f"{click.style('Back-translation:', fg='yellow')} {result.back_translation}")

    except WizzlethorpeError as e:
        click.echo(f"Translation failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
