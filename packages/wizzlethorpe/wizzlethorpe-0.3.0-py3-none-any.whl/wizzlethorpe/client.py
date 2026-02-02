"""Wizzlethorpe API client."""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path

import httpx

from wizzlethorpe.config import get_config_value
from wizzlethorpe.models import (
    AspectRatio,
    Cocktail,
    CocktailsResponse,
    Garnish,
    GeneratedImage,
    ImageQuality,
    ImageType,
    Ingredient,
    Language,
    LinkCode,
    Liquor,
    TranslationResult,
    User,
)

DEFAULT_BASE_URL = "https://wizzlethorpe.com"
CONFIG_DIR = Path.home() / ".config" / "wizzlethorpe"
TOKEN_FILE = CONFIG_DIR / "token"


class WizzlethorpeError(Exception):
    """Base exception for Wizzlethorpe API errors."""


class AuthenticationError(WizzlethorpeError):
    """Authentication failed or required."""


class CocktailsAPI:
    """Cocktails API methods."""

    def __init__(self, client: "WizzlethorpeClient"):
        self._client = client
        self._cache: CocktailsResponse | None = None

    def _fetch(self) -> CocktailsResponse:
        """Fetch and cache cocktails data."""
        if self._cache is None:
            resp = self._client._request("GET", "/api/cocktails")
            self._cache = CocktailsResponse.model_validate(resp)
        return self._cache

    def list(self) -> list[Cocktail]:
        """Get all cocktails.

        Returns:
            List of cocktails (filtered by tier if not authenticated).
        """
        return self._fetch().cocktails

    def get(self, name: str) -> Cocktail | None:
        """Get a cocktail by name.

        Args:
            name: Cocktail name (case-insensitive).

        Returns:
            The cocktail or None if not found.
        """
        name_lower = name.lower()
        return next((c for c in self.list() if c.name.lower() == name_lower), None)

    def liquors(self) -> list[Liquor]:
        """Get all base liquors."""
        return self._fetch().liquors

    def ingredients(self, environment: str | None = None) -> list[Ingredient]:
        """Get ingredients, optionally filtered by environment.

        Args:
            environment: Filter by environment (e.g., "Forest", "Coastal").

        Returns:
            List of ingredients.
        """
        ingredients = self._fetch().ingredients
        if environment:
            ingredients = [i for i in ingredients if environment in i.environments]
        return ingredients

    def garnishes(self) -> list[Garnish]:
        """Get all garnishes."""
        return self._fetch().garnishes


class QuickbrushAPI:
    """Quickbrush image generation API."""

    def __init__(self, client: "WizzlethorpeClient"):
        self._client = client

    def generate(
        self,
        image_type: ImageType,
        prompt: str,
        *,
        context: str | None = None,
        quality: ImageQuality = "auto",
        aspect_ratio: AspectRatio = "square",
        reference_images: list[Path | str] | None = None,
    ) -> GeneratedImage:
        """Generate an image.

        Args:
            image_type: Type of image (character, scene, creature, item).
            prompt: Description of what to generate.
            context: Optional context for the generation.
            quality: Image quality (low, medium, high, auto).
            aspect_ratio: Aspect ratio (square, landscape, portrait, wide).
            reference_images: Optional reference images (up to 4).

        Returns:
            The generated image.

        Raises:
            AuthenticationError: If API key or linked account required.
            WizzlethorpeError: If generation fails.
        """
        data: dict = {
            "type": image_type,
            "text": prompt,
            "quality": quality,
            "aspectRatio": aspect_ratio,
        }
        if context:
            data["prompt"] = context

        # Add API key to request body for BYOK mode
        if self._client.api_key:
            data["apiKey"] = self._client.api_key

        # Encode reference images as base64
        if reference_images:
            refs = []
            for ref_path in reference_images[:4]:
                path = Path(ref_path)
                img_data = path.read_bytes()
                b64 = base64.b64encode(img_data).decode()
                ext = path.suffix.lower().lstrip(".")
                mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(
                    ext, "image/png"
                )
                refs.append(f"data:{mime};base64,{b64}")
            data["referenceImages"] = refs

        resp = self._client._request("POST", "/api/generate", json=data)

        if "error" in resp:
            raise WizzlethorpeError(resp["error"])

        # Decode the image
        image_b64 = resp.get("image", "")
        if image_b64.startswith("data:"):
            image_b64 = image_b64.split(",", 1)[1]
        image_data = base64.b64decode(image_b64)

        return GeneratedImage(
            data=image_data,
            prompt=prompt,
            revised_prompt=resp.get("revisedPrompt"),
            image_type=image_type,
        )

    def character(self, prompt: str, **kwargs) -> GeneratedImage:
        """Generate a character image."""
        return self.generate("character", prompt, **kwargs)

    def scene(self, prompt: str, **kwargs) -> GeneratedImage:
        """Generate a scene image."""
        return self.generate("scene", prompt, **kwargs)

    def creature(self, prompt: str, **kwargs) -> GeneratedImage:
        """Generate a creature image."""
        return self.generate("creature", prompt, **kwargs)

    def item(self, prompt: str, **kwargs) -> GeneratedImage:
        """Generate an item image."""
        return self.generate("item", prompt, **kwargs)


class LanguagesAPI:
    """Languages translation API."""

    def __init__(self, client: "WizzlethorpeClient"):
        self._client = client
        self._cache: list[Language] | None = None

    def list(self) -> list[Language]:
        """Get all available languages.

        Returns:
            List of available languages for translation.
        """
        if self._cache is None:
            resp = self._client._request("GET", "/api/conlang/translate")
            self._cache = [Language.model_validate(lang) for lang in resp.get("languages", [])]
        return self._cache

    def get(self, language_id: str) -> Language | None:
        """Get a language by ID.

        Args:
            language_id: Language ID (e.g., "elvish", "dwarvish").

        Returns:
            The language or None if not found.
        """
        return next((lang for lang in self.list() if lang.id == language_id), None)

    def translate(
        self,
        text: str,
        language: str,
        *,
        include_back_translation: bool = True,
    ) -> TranslationResult:
        """Translate English text into a fantasy language.

        Args:
            text: English text to translate (max 500 characters).
            language: Target language ID (e.g., "elvish", "dwarvish").
            include_back_translation: Include back-translation for verification.

        Returns:
            Translation result with source, target, and optional back-translation.

        Raises:
            WizzlethorpeError: If translation fails or language not found.
        """
        resp = self._client._request(
            "POST",
            "/api/conlang/translate",
            json={
                "text": text,
                "language": language,
                "includeBackTranslation": include_back_translation,
            },
        )

        if not resp.get("success"):
            raise WizzlethorpeError(resp.get("message", "Translation failed"))

        return TranslationResult(
            source=resp["source"],
            target=resp["target"],
            backTranslation=resp.get("backTranslation"),
            language_id=resp["language"]["id"],
            language_name=resp["language"]["name"],
        )


def _get_base_url() -> str:
    """Get base URL from environment or config or default."""
    return (
        os.environ.get("WIZZLETHORPE_BASE_URL")
        or get_config_value("base_url")
        or DEFAULT_BASE_URL
    )


def _get_api_key() -> str | None:
    """Get API key from environment or config."""
    return os.environ.get("OPENAI_API_KEY") or get_config_value("api_key")


class WizzlethorpeClient:
    """Client for Wizzlethorpe Labs APIs.

    Args:
        base_url: API base URL (or set WIZZLETHORPE_BASE_URL env var).
        api_key: OpenAI API key for BYOK generation (or set OPENAI_API_KEY env var).
        token: Session token from device linking.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        token: str | None = None,
    ):
        self.base_url = (base_url or _get_base_url()).rstrip("/")
        self.api_key = api_key or _get_api_key()
        self.token = token or self._load_token()
        self._http = httpx.Client(timeout=120)

        # API namespaces
        self.cocktails = CocktailsAPI(self)
        self.quickbrush = QuickbrushAPI(self)
        self.languages = LanguagesAPI(self)

    def _load_token(self) -> str | None:
        """Load saved token from config."""
        if TOKEN_FILE.exists():
            return TOKEN_FILE.read_text().strip()
        return None

    def _save_token(self, token: str) -> None:
        """Save token to config."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(token)

    def _request(self, method: str, path: str, **kwargs) -> dict:
        """Make an authenticated API request."""
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        resp = self._http.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 401:
            raise AuthenticationError("Authentication required")
        if resp.status_code >= 400:
            raise WizzlethorpeError(f"API error: {resp.status_code} {resp.text}")

        return resp.json()

    def me(self) -> User | None:
        """Get current authenticated user.

        Returns:
            User info or None if not authenticated.
        """
        if not self.token:
            return None
        try:
            resp = self._request("GET", "/api/auth/me")
            if resp.get("authenticated"):
                return User.model_validate(resp["user"])
        except AuthenticationError:
            pass
        return None

    def link(self) -> LinkCode:
        """Start device linking flow.

        Returns:
            Link code to display to user.
        """
        resp = self._request("POST", "/api/auth/link")
        return LinkCode.model_validate(resp)

    def poll_link(self, code: str, timeout: int = 300, poll_interval: int = 3) -> User:
        """Poll for link completion.

        Args:
            code: The link code from link().
            timeout: Max seconds to wait.
            poll_interval: Seconds between polls.

        Returns:
            Authenticated user.

        Raises:
            AuthenticationError: If linking times out or fails.
        """
        start = time.time()
        while time.time() - start < timeout:
            resp = self._request("GET", f"/api/auth/link-status?code={code}")
            if resp.get("status") == "completed":
                self.token = resp["token"]
                self._save_token(self.token)
                return User.model_validate(resp["user"])
            if resp.get("status") == "expired":
                raise AuthenticationError("Link code expired")
            time.sleep(poll_interval)

        raise AuthenticationError("Link timeout")

    def logout(self) -> None:
        """Clear saved authentication."""
        self.token = None
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
