from dataclasses import dataclass
from argparse import ArgumentParser
from typing import Iterable, Dict, List, Set, Tuple
import sys
import re
import click
import requests
import time
from urllib.parse import unquote_plus, quote

@dataclass
class Repository:
    name: str
    result_urls: set[str]
    url: str
    stars: int = -1

    def __str__(self):
        return "{name}\n - stars: {stars},\n - url: {url},\n - results: {results_url}".format(
            name=click.style(self.name, bold=True),
            stars=click.style(self.stars, fg="yellow", bold=True),
            url=click.style(self.url, fg="blue", underline=True),
            results_url=click.style(self.result_urls, fg="blue", underline=True)
        )

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, other):
        return self.url == other.url

    @staticmethod
    def repos_from_search(search_results: list) -> set["Repository"]:
        repos: dict[str, Repository] = {}
        with click.progressbar(search_results, label="Parsing query results") as bar:
            for result in search_results:
                result_url = result["html_url"]
                repo_data = result["repository"]
                repository = Repository(
                    name=repo_data["full_name"],
                    result_urls= {result_url},
                    url=repo_data["html_url"],
                    stars=repo_data["stargazers_count"] if "stargazers_count" in repo_data else -1,
                )
                if repository.url in repos:
                    repos[repository.url].result_urls |= repository.result_urls
                else:
                    repos[repository.url] = repository
                bar.update(1)
        return set(repos.values())

class GithubApi:
    def __init__(self, token):
        self.__session = requests.Session()
        self.__session.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def search(self, query: str) -> set[Repository]:
        url = f"https://api.github.com/search/code?q={query}&per_page=100"
        next_page_pattern = re.compile(r'(?<=<)([\S]*)(?=>; rel=\"next\")', re.IGNORECASE)
        pages_fetched = 0
        pages_remaining = True
        results = []
        while pages_remaining:
            try:
                response = self.__session.get(url, timeout=30)
                # Basic rate-limit handling using reset header if present
                requests_remaining = int(response.headers.get("x-ratelimit-remaining", "1"))
                if response.status_code == 429 or requests_remaining == 0:
                    reset = int(response.headers.get("x-ratelimit-reset", str(int(time.time()) + 60)))
                    sleep_for = max(1, reset - int(time.time()))
                    click.secho(f"\rRate limit hit. Sleeping {sleep_for}s until reset...", fg="red")
                    time.sleep(min(sleep_for, 90))
                    continue
                result = response.json()["items"]
            except requests.RequestException:
                print("Request failed.")
                return set()
            except KeyError:
                return set()
            else:
                pages_fetched += 1
                results.extend(result)
                if "link" not in response.headers:
                    break
                link_header = response.headers["link"]
                pages_remaining = ('rel=\"next\"' in link_header)
                if (pages_remaining):
                    click.secho(f"\rMore results remaining. Fetched {pages_fetched} pages. Fetching next page of results...", fg="yellow", nl=False)
                    match = next_page_pattern.search(link_header)
                    if match:
                        url = unquote_plus(match[0])
                    else:
                        break # failed to extract the next page, better exit
        click.secho("\nSuccess! Parsing query results.", fg="green")
        return Repository.repos_from_search(results)

    def star_count(self, repo_name: str) -> int:
        url =  "https://api.github.com/repos/" + repo_name
        try:
            response = self.__session.get(url, timeout=30)
            return response.json()["stargazers_count"]
        except requests.RequestException:
            print("Request failed.")
            return -1
        except KeyError:
            return -1

    def default_branch_and_sha(self, full_name: str) -> Tuple[str, str]:
        url = f"https://api.github.com/repos/{full_name}"
        r = self.__session.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        return data["default_branch"], data["pushed_at"]  # pushed_at as cache buster only

    def get_branch_sha(self, full_name: str, branch: str) -> str:
        url = f"https://api.github.com/repos/{full_name}/git/refs/heads/{branch}"
        r = self.__session.get(url, timeout=30)
        r.raise_for_status()
        return r.json()["object"]["sha"]

    def get_tree(self, full_name: str, sha: str) -> List[dict]:
        url = f"https://api.github.com/repos/{full_name}/git/trees/{sha}?recursive=1"
        r = self.__session.get(url, timeout=60)
        r.raise_for_status()
        return r.json().get("tree", [])

    def fetch_raw(self, full_name: str, branch: str, path: str) -> str:
        # raw endpoint is faster and avoids extra JSON
        url = f"https://raw.githubusercontent.com/{full_name}/{quote(branch)}/{path}"
        r = self.__session.get(url, timeout=60)
        r.raise_for_status()
        return r.text

def find_matches(text: str, patterns: List[re.Pattern]) -> Dict[str, List[str]]:
    findings: Dict[str, List[str]] = {}
    for pat in patterns:
        hits = []
        for m in pat.finditer(text):
            # capture small context
            start = max(0, m.start() - 40)
            end = min(len(text), m.end() + 40)
            snippet = text[start:end].replace("\n", " ")
            hits.append(snippet)
        if hits:
            findings[pat.pattern] = hits
    return findings

def main():
    parser = ArgumentParser()
    parser.add_argument("-k", "--api-key", required=True, help="GitHub API token. Create one at https://github.com/settings/tokens")
    parser.add_argument("-q", "--query", help="GitHub code search query (e.g., language:js knex.raw \"${\")")
    parser.add_argument("-p", "--pattern", action="append", default=[], help="Regex pattern to scan within repos (can be repeated)")
    parser.add_argument("--min-stars", type=int, default=500, help="Only include repositories with at least this many stars")
    parser.add_argument("--max-files", type=int, default=2000, help="Maximum files to scan per repository")
    parser.add_argument("--max-bytes", type=int, default=200_000, help="Maximum size of file (bytes) to fetch and scan")
    args = parser.parse_args(sys.argv[1:])

    api = GithubApi(args.api_key)

    query = args.query or click.prompt('Enter a search query', type=str, prompt_suffix=">")
    click.secho("Running code search...", bold=True)
    repos = api.search(query)
    if not repos:
        click.secho("No results.", fg="red")
        return

    with click.progressbar(repos, label="Fetching star counts") as bar:
        for repo in repos:
            bar.update(1)
            if repo.stars == -1:
                repo.stars = api.star_count(repo.name)

    repos = sorted([r for r in repos if r.stars >= args.min_stars], key=lambda r: r.stars, reverse=True)
    click.secho(f"Repositories matching query (stars >= {args.min_stars}):", bold=True)
    print("\n".join(str(r) for r in repos))

    if args.pattern:
        compiled = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in args.pattern]
        click.secho("\nScanning repositories for provided regex patterns...", bold=True)
        enriched: List[dict] = []
        for repo in repos:
            try:
                branch, _ = api.default_branch_and_sha(repo.name)
                sha = api.get_branch_sha(repo.name, branch)
                tree = api.get_tree(repo.name, sha)
            except requests.RequestException:
                continue
            files = [t for t in tree if t.get("type") == "blob" and (t.get("size") or 0) <= args.max_bytes]
            files = files[: args.max_files]
            repo_hits: Dict[str, Dict[str, List[str]]] = {}
            with click.progressbar(files, label=f"Scanning {repo.name}") as bar:
                for f in files:
                    bar.update(1)
                    path = f.get("path", "")
                    # quick skip of binaries by extension
                    if re.search(r"\.(png|jpg|jpeg|gif|pdf|zip|gz|ico|lock|min\.js)$", path, re.I):
                        continue
                    try:
                        content = api.fetch_raw(repo.name, branch, path)
                    except requests.RequestException:
                        continue
                    m = find_matches(content, compiled)
                    if m:
                        repo_hits[path] = m
            if repo_hits:
                enriched.append({
                    "repo": repo.name,
                    "url": repo.url,
                    "stars": repo.stars,
                    "matches": repo_hits,
                })
        if enriched:
            click.secho("\nPattern matches:", bold=True)
            for r in enriched:
                click.secho(f"\n{r['repo']} ({r['stars']}★): {r['url']}", fg="green", bold=True)
                for path, pats in r["matches"].items():
                    print(f" - {path}")
                    for pat, snippets in pats.items():
                        print(f"   * /{pat}/")
                        for s in snippets[:3]:
                            print(f"     > {s}")
        else:
            click.secho("No pattern matches found in scanned repositories.", fg="yellow")

if __name__ == "__main__":
    main()