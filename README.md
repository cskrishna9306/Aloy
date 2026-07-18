# Aloy
Wakes up, checks my TODOs, tells me what matters. An Alexa skill + LLM summarizer for daily goals.

## Overview

Say "Alexa, open Aloy" and it will:

1. Fetch my TODOs from a private GitHub repo (`Campaign.md`, `Guild.md`, `Expedition.md`).
2. Hand them to Claude (via AWS Bedrock) along with an Aloy-inspired persona prompt.
3. Read the resulting summary back to me as a short spoken briefing.

The same `Aloy` class also runs standalone from the command line, outside of Alexa entirely.

## Directory structure

```
src/aloy/            Core Python package - the actual "brain"
  agent.py             The Aloy class: fetch_todos(), summarize(), run()
  config.py            Loads env vars (.env) into a Config object
  main.py              CLI entry point (uv run python -m src.aloy.main)
  PERSONA.md           System prompt fed to the model - Aloy's voice/tone

aws/lambda/          Everything needed to package this as a Lambda function
  function.py          ask-sdk request/exception handlers - the Alexa entry point
  requirements.txt     Pinned deps for the deployment package (mirrors pyproject.toml)
  trust-policy.json    IAM trust policy for the Lambda execution role
  bedrock-policy.json  IAM policy granting bedrock:InvokeModel

Taskfile.yml          Build + deploy commands (see below)
pyproject.toml        Project metadata/deps for local dev (uv)
.env.example          Template for the env vars config.py expects
```

`aws/lambda/function.py` and `src/aloy/` are separate because `lambda` is a reserved
Python keyword — the package couldn't be named or imported that way, so the Alexa
handler lives next to (not inside) the core `aloy` package and imports it as
`from src.aloy import Aloy`.

## Local setup

```bash
cp .env.example .env   # fill in GH_PAT, GH_TODO_REPO_OWNER, GH_TODO_REPO_NAME, AWS_REGION
uv sync
uv run python -m src.aloy.main
```

## Deploying to Lambda

Deployment is plain `aws` CLI calls wrapped in `Taskfile.yml` — no CloudFormation/SAM.
Requires the AWS CLI configured with credentials that can manage IAM and Lambda.

**First-time setup:**

```bash
task deploy                                  # builds the zip, creates the IAM role + function
task allow-alexa SKILL_ID=amzn1.ask.skill.xxx   # grants your Alexa skill invoke permission
```

Grab the function's ARN afterward (`aws lambda get-function --function-name aloy --query 'Configuration.FunctionArn'`)
and paste it into the Alexa Developer Console as the skill's endpoint.

**Every deploy after that** is just:

```bash
task deploy
```

This re-zips `aws/lambda/function.py` + `src/` + dependencies and pushes new code/config
to the existing function. `allow-alexa` only needs to run again if the permission is
ever revoked or the skill ID changes.

Individual tasks, if you need them in isolation:

| Task | What it does |
| --- | --- |
| `task package` | Builds `aloy.zip` in the repo root |
| `task ensure-role` | Creates the `aloy-lambda-role` IAM role (idempotent, skips if it exists) |
| `task deploy` | Runs `package` + `ensure-role`, then creates or updates the `aloy` function |
| `task allow-alexa SKILL_ID=...` | Grants the given Alexa skill permission to invoke the function |

## Why "Aloy"?

Named after the protagonist from one of my favorite PS exclusive games, **Horizon: Zero Dawn**! I loveddd the setting of this game in a post-apocalyptic universe where autonomous machines have gone haywire, and Aloy, the MC, is set out to tame this metal wilderness w/ a bow and arrow! 

Does not really align w/ the intent of this project but whatever since I'm running out of project names and seem to be inspired by her while creating this repo haha!
