"""Pydantic models for Wizzlethorpe APIs."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


# === Auth Models ===


class User(BaseModel):
    """Authenticated user info."""

    id: str
    email: str
    name: str
    image_url: str | None = Field(None, alias="imageUrl")
    is_patron: bool = Field(alias="isPatron")
    tier_cents: int = Field(alias="tierCents")
    tier_name: str = Field(alias="tierName")


class LinkCode(BaseModel):
    """Device link code for authentication."""

    code: str = Field(alias="linkCode")
    link_url: str = Field(alias="linkUrl")
    expires_in: int = Field(alias="expiresIn")


# === Cocktails Models ===


class Liquor(BaseModel):
    """Base liquor for cocktails."""

    id: str
    name: str
    color: str
    description: str


class Ingredient(BaseModel):
    """Magical ingredient for cocktails."""

    id: str
    name: str
    color: str
    description: str
    found_in: str = Field(alias="foundIn")
    environments: list[str]
    wishlist_quote: str = Field(alias="wishlistQuote")


class Garnish(BaseModel):
    """Cocktail garnish with modifiers."""

    id: str
    name: str
    description: str
    good_with: list[str] = Field(alias="goodWith")
    bad_with: list[str] = Field(alias="badWith")


class CocktailEffects(BaseModel):
    """Roll effects for a cocktail (1d4)."""

    roll1: str
    roll2: str
    roll3: str
    roll4: str


class Cocktail(BaseModel):
    """A magical cocktail."""

    id: str
    name: str
    description: str
    appearance: str
    liquor_id: str = Field(alias="liquorId")
    ingredient_id: str = Field(alias="ingredientId")
    effects: CocktailEffects


class CocktailsResponse(BaseModel):
    """Response from /api/cocktails endpoint."""

    cocktails: list[Cocktail]
    liquors: list[Liquor]
    ingredients: list[Ingredient]
    garnishes: list[Garnish]
    sample_only: bool = Field(False, alias="sampleOnly")
    total_count: int | None = Field(None, alias="totalCount")


# === Quickbrush Models ===

ImageType = Literal["character", "scene", "creature", "item"]
ImageQuality = Literal["low", "medium", "high", "auto"]
AspectRatio = Literal["square", "landscape", "portrait", "wide"]


class GeneratedImage(BaseModel):
    """A generated image from Quickbrush."""

    data: bytes = Field(exclude=True)
    prompt: str
    revised_prompt: str | None = None
    image_type: ImageType
    format: str = "webp"

    def save(self, path: str | Path) -> Path:
        """Save image to file.

        Args:
            path: Destination path.

        Returns:
            The path where the image was saved.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.data)
        return path

    model_config = {"arbitrary_types_allowed": True}


# === Languages Models ===


class Language(BaseModel):
    """A constructed language available for translation."""

    id: str
    name: str
    description: str


class TranslationResult(BaseModel):
    """Result of a translation request."""

    source: str
    target: str
    back_translation: str | None = Field(None, alias="backTranslation")
    language_id: str
    language_name: str
