"""
Detect project stack by analyzing file markers, package.json, and pyproject.toml.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]


# (marker_path, category, label)
# Categories: language, framework, database, infrastructure, tool
FILE_MARKERS: list[tuple[str, str, str]] = [
    # Languages
    ("package.json", "language", "JavaScript/TypeScript"),
    ("pyproject.toml", "language", "Python"),
    ("setup.py", "language", "Python"),
    ("requirements.txt", "language", "Python"),
    ("go.mod", "language", "Go"),
    ("Cargo.toml", "language", "Rust"),
    ("Gemfile", "language", "Ruby"),
    ("pom.xml", "language", "Java"),
    ("build.gradle", "language", "Java/Kotlin"),
    ("composer.json", "language", "PHP"),
    ("Package.swift", "language", "Swift"),
    ("mix.exs", "language", "Elixir"),
    ("pubspec.yaml", "language", "Dart/Flutter"),

    # Frameworks
    ("next.config.js", "framework", "Next.js"),
    ("next.config.mjs", "framework", "Next.js"),
    ("next.config.ts", "framework", "Next.js"),
    ("nuxt.config.ts", "framework", "Nuxt"),
    ("nuxt.config.js", "framework", "Nuxt"),
    ("svelte.config.js", "framework", "SvelteKit"),
    ("astro.config.mjs", "framework", "Astro"),
    ("vite.config.ts", "framework", "Vite"),
    ("vite.config.js", "framework", "Vite"),
    ("angular.json", "framework", "Angular"),
    ("manage.py", "framework", "Django"),
    ("app.py", "framework", "Flask/FastAPI"),
    ("main.py", "framework", "Python App"),
    ("remix.config.js", "framework", "Remix"),
    ("gatsby-config.js", "framework", "Gatsby"),
    ("expo-app.json", "framework", "Expo"),

    # Databases
    ("prisma/schema.prisma", "database", "Prisma"),
    ("supabase/config.toml", "database", "Supabase"),
    ("drizzle.config.ts", "database", "Drizzle"),
    ("drizzle.config.js", "database", "Drizzle"),
    ("knexfile.js", "database", "Knex"),
    ("ormconfig.json", "database", "TypeORM"),
    ("alembic.ini", "database", "Alembic/SQLAlchemy"),
    ("migrations/", "database", "Database Migrations"),
    ("mongod.conf", "database", "MongoDB"),
    (".sqliterc", "database", "SQLite"),

    # Infrastructure
    ("Dockerfile", "infrastructure", "Docker"),
    ("docker-compose.yml", "infrastructure", "Docker Compose"),
    ("docker-compose.yaml", "infrastructure", "Docker Compose"),
    ("vercel.json", "infrastructure", "Vercel"),
    (".vercel/", "infrastructure", "Vercel"),
    ("netlify.toml", "infrastructure", "Netlify"),
    ("fly.toml", "infrastructure", "Fly.io"),
    ("render.yaml", "infrastructure", "Render"),
    ("railway.json", "infrastructure", "Railway"),
    (".github/workflows/", "infrastructure", "GitHub Actions"),
    ("Procfile", "infrastructure", "Heroku"),
    ("terraform/", "infrastructure", "Terraform"),
    ("k8s/", "infrastructure", "Kubernetes"),
    ("kubernetes/", "infrastructure", "Kubernetes"),
    (".do/app.yaml", "infrastructure", "DigitalOcean App Platform"),

    # Tools
    ("tailwind.config.js", "tool", "Tailwind CSS"),
    ("tailwind.config.ts", "tool", "Tailwind CSS"),
    ("tailwind.config.mjs", "tool", "Tailwind CSS"),
    ("postcss.config.js", "tool", "PostCSS"),
    (".eslintrc.json", "tool", "ESLint"),
    (".eslintrc.js", "tool", "ESLint"),
    ("eslint.config.js", "tool", "ESLint"),
    (".prettierrc", "tool", "Prettier"),
    ("biome.json", "tool", "Biome"),
    ("tsconfig.json", "tool", "TypeScript"),
    ("jest.config.js", "tool", "Jest"),
    ("vitest.config.ts", "tool", "Vitest"),
    ("pytest.ini", "tool", "Pytest"),
    ("pyproject.toml", "tool", "Python Tooling"),
    (".env", "tool", "Environment Variables"),
    (".env.example", "tool", "Environment Variables"),
    ("CLAUDE.md", "tool", "Claude Code"),
    (".cursor/", "tool", "Cursor"),
    ("turbo.json", "tool", "Turborepo"),
    ("pnpm-workspace.yaml", "tool", "pnpm Workspaces"),
    ("lerna.json", "tool", "Lerna"),
    ("nx.json", "tool", "Nx"),
    ("Makefile", "tool", "Make"),
    (".husky/", "tool", "Husky"),
    ("commitlint.config.js", "tool", "Commitlint"),
    ("storybook/", "tool", "Storybook"),
    (".storybook/", "tool", "Storybook"),
]

# Known npm dependencies → framework/tool
NPM_MARKERS: dict[str, tuple[str, str]] = {
    "react": ("framework", "React"),
    "next": ("framework", "Next.js"),
    "vue": ("framework", "Vue"),
    "nuxt": ("framework", "Nuxt"),
    "svelte": ("framework", "Svelte"),
    "@angular/core": ("framework", "Angular"),
    "express": ("framework", "Express"),
    "fastify": ("framework", "Fastify"),
    "hono": ("framework", "Hono"),
    "prisma": ("database", "Prisma"),
    "@supabase/supabase-js": ("database", "Supabase"),
    "drizzle-orm": ("database", "Drizzle"),
    "mongoose": ("database", "MongoDB/Mongoose"),
    "tailwindcss": ("tool", "Tailwind CSS"),
    "typescript": ("tool", "TypeScript"),
    "vitest": ("tool", "Vitest"),
    "jest": ("tool", "Jest"),
    "eslint": ("tool", "ESLint"),
    "prettier": ("tool", "Prettier"),
    "storybook": ("tool", "Storybook"),
    "zustand": ("tool", "Zustand"),
    "redux": ("tool", "Redux"),
    "@trpc/server": ("tool", "tRPC"),
    "zod": ("tool", "Zod"),
    "stripe": ("tool", "Stripe"),
    "resend": ("tool", "Resend"),
}

# Known Python dependencies → framework/tool
PYTHON_MARKERS: dict[str, tuple[str, str]] = {
    "fastapi": ("framework", "FastAPI"),
    "django": ("framework", "Django"),
    "flask": ("framework", "Flask"),
    "starlette": ("framework", "Starlette"),
    "sqlalchemy": ("database", "SQLAlchemy"),
    "prisma": ("database", "Prisma"),
    "alembic": ("database", "Alembic"),
    "pytest": ("tool", "Pytest"),
    "celery": ("tool", "Celery"),
    "redis": ("tool", "Redis"),
    "pydantic": ("tool", "Pydantic"),
    "typer": ("tool", "Typer"),
    "click": ("tool", "Click"),
    "httpx": ("tool", "HTTPX"),
    "boto3": ("infrastructure", "AWS SDK"),
}


@dataclass
class DetectionResult:
    """Result of project stack detection."""

    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    databases: list[str] = field(default_factory=list)
    infrastructure: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    package_json: Optional[dict] = None
    pyproject: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "languages": self.languages,
            "frameworks": self.frameworks,
            "databases": self.databases,
            "infrastructure": self.infrastructure,
            "tools": self.tools,
        }

    @property
    def is_empty(self) -> bool:
        return not any([
            self.languages, self.frameworks, self.databases,
            self.infrastructure, self.tools,
        ])


def _add_unique(lst: list[str], value: str) -> None:
    if value not in lst:
        lst.append(value)


def _parse_package_json(path: Path) -> Optional[dict]:
    pkg_path = path / "package.json"
    if not pkg_path.exists():
        return None
    try:
        with open(pkg_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _parse_pyproject(path: Path) -> Optional[dict]:
    pp_path = path / "pyproject.toml"
    if not pp_path.exists() or tomllib is None:
        return None
    try:
        with open(pp_path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return None


def detect(path: Path) -> DetectionResult:
    """Detect languages, frameworks, databases, infrastructure, and tools."""
    result = DetectionResult()
    category_map = {
        "language": result.languages,
        "framework": result.frameworks,
        "database": result.databases,
        "infrastructure": result.infrastructure,
        "tool": result.tools,
    }

    # 1. Check file markers
    for marker, category, label in FILE_MARKERS:
        target = path / marker
        if target.exists():
            _add_unique(category_map[category], label)

    # 2. Parse package.json dependencies
    pkg = _parse_package_json(path)
    if pkg:
        result.package_json = pkg
        all_deps = {}
        all_deps.update(pkg.get("dependencies", {}))
        all_deps.update(pkg.get("devDependencies", {}))

        for dep_name, (category, label) in NPM_MARKERS.items():
            if dep_name in all_deps:
                _add_unique(category_map[category], label)

    # 3. Parse pyproject.toml dependencies
    pyproj = _parse_pyproject(path)
    if pyproj:
        result.pyproject = pyproj
        # Check [project.dependencies] and [tool.poetry.dependencies]
        deps: list[str] = []
        proj_deps = pyproj.get("project", {}).get("dependencies", [])
        if isinstance(proj_deps, list):
            deps.extend(proj_deps)
        poetry_deps = pyproj.get("tool", {}).get("poetry", {}).get("dependencies", {})
        if isinstance(poetry_deps, dict):
            deps.extend(poetry_deps.keys())

        for dep_str in deps:
            dep_name = dep_str.split(">=")[0].split("==")[0].split("<")[0].split("[")[0].strip().lower()
            if dep_name in PYTHON_MARKERS:
                category, label = PYTHON_MARKERS[dep_name]
                _add_unique(category_map[category], label)

    return result


def has_existing_code(path: Path) -> bool:
    """Check if a directory contains existing code (used by init)."""
    code_indicators = [
        "package.json", "pyproject.toml", "setup.py", "requirements.txt",
        "go.mod", "Cargo.toml", "Gemfile", "pom.xml", "composer.json",
        "Makefile", "manage.py", "main.py", "app.py", "index.js",
        "index.ts", "src/", "lib/", "app/",
    ]
    for indicator in code_indicators:
        if (path / indicator).exists():
            return True
    return False
