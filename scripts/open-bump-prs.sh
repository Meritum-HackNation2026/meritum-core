#!/usr/bin/env bash
# After a push to main (workflow bump-dependents.yml): opens or updates PRs that move
# meritum-backend and meritum-worker to this commit, and refreshes the contract copy in
# meritum-design-system when the contracts changed. One rolling branch per repo, chore/bump-core.
# Needs BOT_TOKEN: a fine-grained token with Contents and Pull requests read/write on those
# three repos and Contents read on meritum-core. Uses git, curl, jq and uv.
set -euo pipefail

org=Meritum-HackNation2026
branch=chore/bump-core
sha=$(git rev-parse HEAD)
short=${sha:0:7}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# Process-scoped git config: clones, pushes and uv's fetch of meritum-core (ssh:// in uv.lock)
# go over https with the token. Never written to the runner's global gitconfig.
export GIT_CONFIG_COUNT=2
export GIT_CONFIG_KEY_0="url.https://x-access-token:${BOT_TOKEN}@github.com/.insteadOf" GIT_CONFIG_VALUE_0="ssh://git@github.com/"
export GIT_CONFIG_KEY_1="url.https://x-access-token:${BOT_TOKEN}@github.com/.insteadOf" GIT_CONFIG_VALUE_1="https://github.com/"
bot=(-c user.name="github-actions[bot]" -c user.email="41898282+github-actions[bot]@users.noreply.github.com")

open_pr() { # repo base title body
  local code
  code=$(curl -sS -o /dev/null -w '%{http_code}' -X POST \
    -H "Authorization: Bearer $BOT_TOKEN" -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/$org/$1/pulls" \
    -d "$(jq -n --arg t "$3" --arg h "$branch" --arg b "$2" --arg body "$4" '{title: $t, head: $h, base: $b, body: $body}')")
  case $code in
    201) echo "$1: PR opened" ;;
    422) echo "$1: PR already open, branch updated" ;;
    *) echo "::error::$1: creating the PR failed (HTTP $code)" && return 1 ;;
  esac
}

push_if_changed() { # dir repo base message body
  if git -C "$1" diff --quiet; then
    echo "$2: already up to date"
    return
  fi
  git -C "$1" "${bot[@]}" commit -qam "$4"
  git -C "$1" push -qf origin "HEAD:refs/heads/$branch"
  open_pr "$2" "$3" "$4" "$5"
}

for repo in meritum-backend meritum-worker; do
  dir=$work/$repo
  # backend and worker keep develop as their integration branch
  git clone -q --depth 1 --branch develop "https://github.com/$org/$repo.git" "$dir"
  sed -i -E "s|(meritum-core\.git\", rev = \")[0-9a-f]{40}\"|\1$sha\"|" "$dir/pyproject.toml"
  grep -q "rev = \"$sha\"" "$dir/pyproject.toml" || { echo "::error::$repo does not pin meritum-core by rev"; exit 1; }
  (cd "$dir" && uv lock --quiet --upgrade-package meritum-core)
  push_if_changed "$dir" "$repo" develop "Podbij meritum-core do $short" \
    "Automatyczne podbicie po zmianie w meritum-core main ($sha). Przed scaleniem sprawdź CI tego PR."
done

ds=$work/meritum-design-system
git clone -q --depth 1 "https://github.com/$org/meritum-design-system.git" "$ds"
c=$ds/contracts
# The contracts are a package (src/meritum_core/checks/contracts/), so the copy holds
# only what consumers read: the generated files and the examples.
if cmp -s contracts/examples.json "$c/examples.json" &&
  cmp -s contracts/meritum.schema.json "$c/meritum.schema.json" &&
  cmp -s contracts/meritum.ts "$c/meritum.ts"; then
  echo "meritum-design-system: contracts unchanged"
  exit 0
fi
# Mirrors contracts/sync.sh in meritum-design-system; keep the two in step (sync.sh still
# fetches the former checks/contracts.py and must drop it too).
cp contracts/examples.json contracts/meritum.schema.json contracts/meritum.ts "$c/"
printf 'meritum-core %s\n' "$sha" >"$c/SOURCE"
(cd "$c" && sha256sum examples.json meritum.schema.json meritum.ts >SHA256SUMS)
push_if_changed "$ds" meritum-design-system main "Odśwież kopię kontraktów z meritum-core $short" \
  "Automatyczna kopia kontraktów z meritum-core main ($sha), jak z contracts/sync.sh."
