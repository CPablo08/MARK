"""GitHub API helpers (personal install — uses GITHUB_TOKEN from env)."""

import httpx

from mark_core.config import get_settings

_GH_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _auth_headers() -> dict[str, str]:
    settings = get_settings()
    if not settings.github_token:
        raise ValueError(
            "GITHUB_TOKEN is not set. Add a personal access token to .env "
            "(classic PAT with `repo` scope, or fine-grained with repository read)."
        )
    return {**_GH_HEADERS, "Authorization": f"Bearer {settings.github_token}"}


async def get_authenticated_user() -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get("https://api.github.com/user", headers=_auth_headers())
        if r.status_code == 401:
            return "GitHub rejected the token. Check GITHUB_TOKEN in .env."
        r.raise_for_status()
        data = r.json()
    login = data.get("login", "unknown")
    name = data.get("name") or ""
    public_repos = data.get("public_repos", 0)
    lines = [f"GitHub account: **{login}**"]
    if name:
        lines.append(f"Name: {name}")
    lines.append(f"Public repositories: {public_repos}")
    return "\n".join(lines)


async def list_repositories() -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            "https://api.github.com/user/repos",
            headers=_auth_headers(),
            params={"per_page": 100, "sort": "updated", "affiliation": "owner,collaborator,organization_member"},
        )
        if r.status_code == 401:
            return "GitHub rejected the token. Check GITHUB_TOKEN in .env."
        r.raise_for_status()
        repos = r.json()

    if not repos:
        return "No repositories found for this token."

    lines = [f"**{len(repos)} repositories** (most recently updated):\n"]
    for repo in repos[:40]:
        name = repo.get("full_name", repo.get("name", "?"))
        private = "private" if repo.get("private") else "public"
        desc = (repo.get("description") or "").strip()
        line = f"- `{name}` ({private})"
        if desc:
            line += f" — {desc[:80]}"
        lines.append(line)
    if len(repos) > 40:
        lines.append(f"\n…and {len(repos) - 40} more.")
    return "\n".join(lines)
