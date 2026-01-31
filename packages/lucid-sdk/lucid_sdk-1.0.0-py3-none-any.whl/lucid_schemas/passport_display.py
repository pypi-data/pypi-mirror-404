"""Passport display configuration schemas."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PassportDisplayMode(str, Enum):
    """Mode for displaying AI Passport to end users."""
    BANNER = "banner"
    FLOATING = "floating"
    PAGE_ONLY = "page_only"
    HEADERS_ONLY = "headers_only"


class BannerPosition(str, Enum):
    """Position of the passport banner."""
    TOP = "top"
    BOTTOM = "bottom"


class BannerTheme(str, Enum):
    """Theme for the passport banner."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class PassportDisplayConfig(BaseModel):
    """User-configurable passport display settings."""
    mode: PassportDisplayMode = Field(default=PassportDisplayMode.BANNER)
    banner_position: BannerPosition = Field(default=BannerPosition.TOP, alias="bannerPosition")
    banner_collapsed_default: bool = Field(default=False, alias="bannerCollapsedDefault")
    banner_theme: BannerTheme = Field(default=BannerTheme.AUTO, alias="bannerTheme")
    enable_browser_extension_prompt: bool = Field(default=True, alias="enableBrowserExtensionPrompt")

    # Advanced options
    custom_css_url: Optional[str] = Field(default=None, alias="customCssUrl", description="Custom banner styling URL")
    passport_page_logo_url: Optional[str] = Field(default=None, alias="passportPageLogoUrl", description="Org branding on passport page")

    model_config = ConfigDict(populate_by_name=True)
