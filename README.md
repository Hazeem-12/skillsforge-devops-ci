# SkillsForge CI Demo

A small Flask service (3 endpoints) with a four-stage GitHub Actions pipeline: **lint -> test -> build -> package**.

| Endpoint | Description |
|---|---|
| `GET /health` | Returns status and version |
| `GET /add?a=1&b=2` | Adds two numbers (400 on bad input) |
| `GET /greet/<name>` | Returns a greeting |

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt     # pinned versions

python -m app.main                      # run the app on http://localhost:8000
flake8                                  # lint (config in .flake8)
pytest -q                               # 7 unit tests
python -m build --wheel                 # build output: dist/*.whl
```

Docker (needs the wheel from the build step):

```bash
docker build -t skillsforge-demo .
docker run -p 8000:8000 skillsforge-demo
curl localhost:8000/health
```

## Evidence

Fill in the links after running `scripts/evidence.sh` (see that file).

| Evidence | Link |
|---|---|
| Green run, all four jobs passing | EVIDENCE_GREEN_RUN |
| PR 1: lint error (test, build, package skipped) | EVIDENCE_PR_LINT |
| PR 2: failing test (build skipped) | EVIDENCE_PR_TEST |
| PR 3: broken build (package skipped) | EVIDENCE_PR_BUILD |
| Cold run (cache miss) | EVIDENCE_COLD_RUN, duration: COLD_TIME |
| Warm run, same commit (cache hit) | EVIDENCE_WARM_RUN, duration: WARM_TIME |

## Pipeline design

**1. Stage order.** `lint` is the cheapest and fastest check, so it runs first; `test` is next; `build` only makes sense once the code is valid and tested; `package` last because it is the most expensive and only needed for code that is releasable. Each stage is chained with `needs`, so the pipeline fails as early and as cheaply as possible. I ran lint and test **in sequence**. Running them in parallel would cut wall-clock time (about the length of the slower job instead of the sum) but would spend runner minutes on tests for code that fails lint, and it adds a second dependency install. For a small project where lint takes seconds, sequence costs little time and saves minutes; for a large test suite I would switch to parallel.

**2. Caching.** I cache pip's download cache (`~/.cache/pip`) with `actions/cache`. The key is `pip-<OS>-py<version>-<hash of requirements.txt and requirements-dev.txt>`. When a lockfile changes, the hash changes, the key no longer matches, so the run misses the cache, installs fresh, and saves a new cache under the new key. If the key were a fixed string such as `deps`, the cache would be restored forever and never updated: after upgrading or adding a dependency the old cache would be used (stale or missing packages, hard-to-explain differences between CI and local), and because a cache entry for an existing key is immutable, the new packages could never be saved.

**3. Fail-fast.** `test` has `needs: lint`, `build` has `needs: test`, `package` has `needs: build`. When a needed job fails, GitHub marks the dependents as skipped.
- *Lint-error PR:* `lint` fails (`flake8`); `test`, `build`, `package` are skipped (`needs: lint` chain). 
- *Failing-test PR:* `lint` passes, `test` fails (`pytest`); `build` and `package` skipped (`needs: test`, `needs: build`). 
- *Broken-build PR:* `lint` and `test` pass, `build` fails (`python -m build`); `package` skipped (`needs: build`). 
In all three, `package` is also excluded on pull requests by `if: github.event_name == 'push'`.

**4. Speed.** Cold run: COLD_TIME. Warm run: WARM_TIME. The difference is the dependency install: on a cold run pip downloads every package from PyPI, on a warm run it restores them from the cache and only installs locally. Cancelling older runs (`concurrency` with `cancel-in-progress: true`, grouped by workflow and ref) helps when someone pushes three commits in two minutes: only the newest commit is worth checking, so the first two runs are cancelled and their runner minutes are not spent, results arrive sooner and the queue stays short.

**5. Safety.** To push the image, the package job would log in to the registry with `docker/login-action` using a registry username and token stored as **GitHub encrypted secrets** (preferably in a protected *environment* with required reviewers, and restricted to the `package` job), never in the repository. Better still, use short-lived credentials through OIDC or the built-in `GITHUB_TOKEN` with `packages: write` on that job only. Pull requests from forks must not get secrets because the PR author controls the code that runs: a malicious workflow change or test could print or send the secret to an attacker. GitHub therefore does not pass secrets to fork PRs, and the `package` job does not run on pull requests at all.

**6. Improve it.** (a) *Vulnerability scanning and SHA-pinned actions:* add Trivy for the image, `pip-audit` for dependencies, and Dependabot, plus pinning third-party actions to commit SHAs; this solves supply-chain risk, which the pipeline currently does not check. (b) *Push the image to a registry (GHCR) on tags with a version tag and a build cache, and a test matrix over several Python versions:* this solves the fact that the image is only built and smoke-tested, never published, and that the app is only verified on one Python version.

## Assumptions

- Python 3.12 on `ubuntu-latest`; `requirements.txt` with exact versions is the lockfile.
- The package job builds and smoke-tests the Docker image but does not push it, since the task says not to store secrets in the repository.
- Timings vary with GitHub runner load; the cold/warm figures are from the linked runs.
