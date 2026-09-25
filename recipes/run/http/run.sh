#!/bin/sh
# Read a French energy diagnostic (DPE) with the cookbook's DPE extraction method, over plain HTTP: start the run, poll its status,
# then read its results.
#
#     sh run.sh <document URL>    starts a run on the document, follows it, and prints the method's output as JSON
#     sh run.sh --run <run id>    follows a run already started, by its id alone, and prints its output
#
# PIPELEX_API_KEY must be set, and each start spends inference credit; following a run spends none. The script needs curl and jq.
# Progress goes to stderr and the output to stdout, so `sh run.sh <document URL> > dpe.json` saves it. WAIT_SECONDS bounds the wait,
# twenty minutes by default; with WAIT_SECONDS=0 the script reads the run's status once and exits.
#
# The exit status tells a scheduler what to do next: 0 with the output; 3 while the run is still going, and 4 when the API was out of
# reach, answered with a server error or answered in a way the script cannot read, both worth asking again with --run, although a
# start that ends with 4 returned no run id; 1 when the run ended without a result, and 5 when the API refused the request (a refused
# key, an input the method does not accept, an unknown run id), both final; 2 when the script was called wrongly.

set -u

METHOD_REF="github.com/Pipelex/pipelex-cookbook/extract_dpe@v0.18.0"
API_URL="https://api.pipelex.com"
WAIT_SECONDS="${WAIT_SECONDS:-1200}"
POLL_SECONDS=5

RUN_FAILED=1
USAGE=2
STILL_RUNNING=3
UNREACHABLE=4
REFUSED=5

say() {
  printf '%s\n' "$*" >&2
}

usage() {
  say "usage: sh run.sh <document URL> | sh run.sh --run <run id>"
  exit "$USAGE"
}

for tool in curl jq; do
  command -v "$tool" >/dev/null 2>&1 || { say "$tool is needed, and it is not installed"; exit "$USAGE"; }
done
[ -n "${PIPELEX_API_KEY:-}" ] || { say "PIPELEX_API_KEY is not set: create a key at https://app.pipelex.com"; exit "$USAGE"; }
case $WAIT_SECONDS in
  '' | *[!0-9]*) say "WAIT_SECONDS must be a whole number of seconds"; exit "$USAGE" ;;
esac

WORK_DIR=$(mktemp -d) || exit "$USAGE"
trap 'rm -rf "$WORK_DIR"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# One call to the API, which leaves the answer's body in $WORK_DIR/body, its headers in $WORK_DIR/headers, and its HTTP status in
# $http_status, 000 when no answer came. The key reaches curl on its standard input as a line of configuration, never as an argument,
# so it does not show in the process list, and nothing here prints it.
call() {
  method=$1
  path=$2
  shift 2
  http_status=$(printf 'header = "Authorization: Bearer %s"\n' "$PIPELEX_API_KEY" |
    curl --silent --show-error --config - --connect-timeout 30 --request "$method" \
      --output "$WORK_DIR/body" --dump-header "$WORK_DIR/headers" --write-out '%{http_code}' "$@" "$API_URL$path") || http_status=000
}

# The answer's body, cut to its first two thousand bytes, to say why a call did not succeed.
answer() {
  if [ "$http_status" = 000 ]; then
    printf 'no answer'
  else
    printf 'HTTP %s: ' "$http_status"
    dd if="$WORK_DIR/body" bs=2000 count=1 2>/dev/null
  fi
}

# The wait before the next poll: the Retry-After header's seconds when the API asks for longer than POLL_SECONDS.
next_delay() {
  retry_after=$(tr -d '\r' <"$WORK_DIR/headers" | awk -F': *' 'tolower($1) == "retry-after" { print $2; exit }')
  case $retry_after in
    '' | *[!0-9]*) echo "$POLL_SECONDS" ;;
    *) if [ "$retry_after" -gt "$POLL_SECONDS" ]; then echo "$retry_after"; else echo "$POLL_SECONDS"; fi ;;
  esac
}

# A call that got no answer, or a server error, ends the script with 4; any other refusal with 5.
exit_on_error() {
  case $http_status in
    000 | 429 | 5??) say "$1: $(answer)"; exit "$UNREACHABLE" ;;
    *) say "$1: $(answer)"; exit "$REFUSED" ;;
  esac
}

# POST /v1/start with the method's address and the document, and set RUN_ID. The API answers 202 with the run's id at once, before the
# method has done anything. The generous time limit is for a first start at a tag, which the API fetches before it answers.
start_run() {
  body=$(jq -n -c --arg method_ref "$METHOD_REF" --arg url "$1" '{method_ref: $method_ref, inputs: {document: {url: $url}}}') || exit "$USAGE"
  call POST /v1/start --max-time 1200 --header "Content-Type: application/json" --data "$body"
  case $http_status in
    2??) ;;
    *) exit_on_error "the API did not start the run" ;;
  esac
  RUN_ID=$(jq -r '.pipeline_run_id // empty' "$WORK_DIR/body" 2>/dev/null) || RUN_ID=
  if [ -z "$RUN_ID" ]; then
    say "the API answered the start without a run id: $(answer)"
    exit "$UNREACHABLE"
  fi
  say "started $RUN_ID"
  jq -r '.method_provenance // empty | "method \(.address) at \(.tag // "no tag"), commit \(.commit_sha)"' "$WORK_DIR/body" >&2 2>/dev/null || true
}

# Say why a run ended without a result: its status, and the error its status record carries, when it carries one.
say_failure() {
  say "run $RUN_ID ended $1"
  jq -c '.error // empty' "$WORK_DIR/body" >&2 2>/dev/null || true
}

# GET /v1/runs/{id}/status until the run ends or the wait does, then GET /v1/runs/{id}/results once it has completed.
follow_run() {
  started_at=$(date +%s)
  deadline=$((started_at + WAIT_SECONDS))
  while :; do
    call GET "/v1/runs/$RUN_ID/status" --max-time 60
    [ "$http_status" = 200 ] || exit_on_error "could not read the status of run $RUN_ID"
    run_status=$(jq -r '.status // empty' "$WORK_DIR/body" 2>/dev/null) || run_status=
    degraded=$(jq -r '.degraded // false' "$WORK_DIR/body" 2>/dev/null) || degraded=false
    delay=$(next_delay)
    case $run_status in
      '')
        say "the status of run $RUN_ID came back without a status: $(answer)"
        exit "$UNREACHABLE"
        ;;
      COMPLETED)
        call GET "/v1/runs/$RUN_ID/results" --max-time 60
        case $http_status in
          200)
            if ! jq -e '.main_stuff != null' "$WORK_DIR/body" >/dev/null 2>&1; then
              say "the results of run $RUN_ID carry no output: $(answer)"
              exit "$UNREACHABLE"
            fi
            jq '.main_stuff' "$WORK_DIR/body"
            say "run $RUN_ID completed"
            exit 0
            ;;
          # The results of a completed run can take a moment to be readable: 202 and 503 both mean asking again.
          202 | 503)
            run_status="COMPLETED, its results not readable yet,"
            delay=$(next_delay)
            ;;
          409) say "run $RUN_ID has no result: $(answer)"; exit "$RUN_FAILED" ;;
          *) exit_on_error "could not read the results of run $RUN_ID" ;;
        esac
        ;;
      FAILED | CANCELLED | TERMINATED | TIMED_OUT)
        say_failure "$run_status"
        exit "$RUN_FAILED"
        ;;
    esac
    now=$(date +%s)
    # A degraded status is the last one the API knew, not a new reading: the run is not stuck, only unobserved for a moment.
    if [ "$degraded" = true ]; then note=" (last known)"; else note=""; fi
    if [ "$now" -ge "$deadline" ]; then
      say "run $RUN_ID is still $run_status$note after the wait; follow it later with: sh run.sh --run $RUN_ID"
      exit "$STILL_RUNNING"
    fi
    say "… $run_status$note after $((now - started_at))s"
    remaining=$((deadline - now))
    [ "$delay" -le "$remaining" ] || delay=$remaining
    sleep "$delay"
  done
}

case ${1:-} in
  -h | --help)
    say "usage: sh run.sh <document URL> | sh run.sh --run <run id>"
    exit 0
    ;;
  --run)
    [ $# -eq 2 ] || usage
    RUN_ID=$2
    case $RUN_ID in
      '' | *[!A-Za-z0-9_-]*) say "a run id holds only letters, digits, - and _, such as run_8bf12c67-…"; exit "$USAGE" ;;
    esac
    ;;
  http://* | https://* | pipelex-storage://*)
    [ $# -eq 1 ] || usage
    start_run "$1"
    ;;
  *)
    say "the document must be a URL the API can fetch: an http(s) link, or a pipelex-storage:// uri"
    usage
    ;;
esac
follow_run
