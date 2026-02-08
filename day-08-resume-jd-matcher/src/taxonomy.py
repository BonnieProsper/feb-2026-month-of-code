from typing import Dict


SKILL_TAXONOMY: Dict[str, str] = {
    # Languages
    "python": "Languages",
    "java": "Languages",
    "javascript": "Languages",
    "sql": "Languages",

    # Frameworks
    "django": "Frameworks",
    "flask": "Frameworks",
    "fastapi": "Frameworks",
    "react": "Frameworks",

    # Tooling
    "docker": "Tooling",
    "git": "Tooling",
    "pytest": "Tooling",

    # Cloud / Platforms
    "aws": "Cloud / Platforms",
    "gcp": "Cloud / Platforms",
    "azure": "Cloud / Platforms",

    # Concepts
    "rest": "Concepts",
    "api": "Concepts",
    "microservices": "Concepts",
}


def classify_skill(term: str) -> str:
    return SKILL_TAXONOMY.get(term.lower(), "Other")
