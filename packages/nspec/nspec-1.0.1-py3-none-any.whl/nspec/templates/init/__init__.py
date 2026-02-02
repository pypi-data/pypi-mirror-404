"""Init templates for nspec project scaffolding.

Each module provides a `render(**kwargs) -> str` function that returns
the template content with substitutions applied.
"""

from nspec.templates.init.ci_cloudbuild import render as render_ci_cloudbuild
from nspec.templates.init.ci_github import render as render_ci_github
from nspec.templates.init.ci_gitlab import render as render_ci_gitlab
from nspec.templates.init.nspec_mk import render as render_nspec_mk

__all__ = [
    "render_ci_cloudbuild",
    "render_ci_github",
    "render_ci_gitlab",
    "render_nspec_mk",
]
