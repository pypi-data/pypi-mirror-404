# dockchangelog

check docker updates with github release notes

## what it does

- finds docker compose services in your directory
- checks if updates are available
- fetches release notes from github
- shows what changed in a clean, readable format

**safe by default** - this tool only reads information, it doesn't modify your containers

## installation

### using uv (recommended)

```bash
# install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# install dockchangelog
uv tool install dockchangelog
```

### using pipx

```bash
pipx install dockchangelog
```

### using pip

```bash
pip install dockchangelog
```

## quick start

```bash
# check for updates in current directory
dockchangelog check

# check specific directory
dockchangelog check --compose-dir /path/to/composes

# check specific service
dockchangelog check --service myapp
```

## example output

```
dockchangelog - checking for updates...

• database: no github mapping found

⚠  app-backend: update available
   Current: latest
   Latest:  v2.5.0
   Published: 2026-01-15

   ✨ Features:
      • added new api endpoints
      • improved performance by 40%
      • added support for webhooks

   🐛 Fixes:
      • fixed memory leak in background jobs
      • resolved connection timeout issues

   https://github.com/example/app-backend/releases/tag/v2.5.0

Press u to mark for update, Enter to skip, Ctrl+C to stop... u
✓ app-backend marked for update

⚠  monitoring: update available
   Current: latest
   Latest:  v3.1.0
   Published: 2026-01-20

   ✨ Features:
      • new dashboard widgets
      • improved alerting system

   🐛 Fixes:
      • fixed graph rendering issues

   https://github.com/example/monitoring/releases/tag/v3.1.0

Press u to mark for update, Enter to skip, Ctrl+C to stop... 

────────────────────────────────────────────────────────────
Found 2 updates available

Services marked for update:

  • app-backend
    latest → v2.5.0
    /home/user/composes/app-backend/compose.yml

To update these services, run:

# Copy and paste this script:

cd /home/user/composes/app-backend && docker compose pull app-backend && docker compose up -d app-backend && \
```

## configuration

create a config file to map images to github repos:

```bash
dockchangelog init
```

this creates `config.yml`:

```yaml
# map docker images to github repositories
image_mappings:
  ghcr.io/user/myapp:latest: user/myapp
  custom/image:latest: owner/repo

# auto-detect repos from docker labels
auto_detect_from_labels: true

# github api token (optional, increases rate limit)
github_token: ${GITHUB_TOKEN}
```

### github token (optional)

without a token: 60 requests/hour  
with a token: 5000 requests/hour

```bash
# set environment variable
export GITHUB_TOKEN=your_token_here

# or put in config.yml
github_token: ${GITHUB_TOKEN}
```

get a token at: https://github.com/settings/tokens

## how it finds repositories

dockchangelog tries multiple methods to map docker images to github repos:

1. **config file** - explicit mappings in `config.yml`
2. **docker labels** - reads `org.opencontainers.image.source` label
3. **heuristics** - smart guessing based on image name
   - `ghcr.io/owner/repo` → `owner/repo`
   - `owner/repo` (docker hub) → `owner/repo`
4. **common mappings** - known popular images

## requirements

- docker
- docker compose
- python 3.8+

## commands

### check

check for updates (main command):

```bash
dockchangelog check                      # current directory, running containers only
dockchangelog check --compose-dir /path  # specific directory
dockchangelog check --service myapp      # specific service
dockchangelog check --include-stopped    # check all containers (including stopped)
dockchangelog check --sudo               # use sudo for docker commands
dockchangelog check --no-interactive     # disable interactive tagging
dockchangelog check --no-cache           # disable cache
```

### init

create example config file:

```bash
dockchangelog init                       # creates config.yml
dockchangelog init --output custom.yml   # custom location
```

### version

show version:

```bash
dockchangelog version
```

## tips

- **by default, only running containers are checked** - use `--include-stopped` to check all
- run from the parent directory containing your compose files
- use `--service` to check one service quickly
- set `GITHUB_TOKEN` environment variable to avoid rate limits
- cache is stored in `~/.cache/dockchangelog` (expires after 24 hours)
- use `--sudo` on systems where docker requires sudo
- press `u` to tag services for update, get a single command to run them all

## exit codes

- `0` - all services up to date
- `1` - updates available

useful for scripts:

```bash
if dockchangelog check; then
    echo "all up to date"
else
    echo "updates available"
fi
```

## troubleshooting

**no services found**
- make sure you have `compose.yml` or `docker-compose.yml` files
- try specifying `--compose-dir` explicitly

**no github mapping found**
- add explicit mapping in `config.yml`
- check if image has `org.opencontainers.image.source` label
- some official images (postgres, nginx) don't have github releases

**rate limit exceeded**
- set up a github token (see configuration section)
- wait for rate limit to reset (1 hour)

## license

MIT license - see license file for details

## contributing

contributions welcome! this is a simple, focused tool - let's keep it that way.

see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## development

```bash
# clone the repo
git clone https://github.com/yourusername/dockchangelog
cd dockchangelog

# install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# create virtual environment and install
uv venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on windows
uv pip install -e ".[dev]"

# run tests
pytest
```
