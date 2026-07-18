# SAM's custom build method only knows how to shell out to `make`, so this
# target just delegates to Taskfile.yml, where the real build steps live.
build-AloyFunction:
	task package ARTIFACTS_DIR="$(ARTIFACTS_DIR)"
