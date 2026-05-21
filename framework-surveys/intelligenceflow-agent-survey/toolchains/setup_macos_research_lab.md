# macOS research lab setup

## Host requirements

- Apple silicon Mac preferred for Apple Intelligence and arm64e shared-cache parity.
- Current macOS build with Apple Intelligence features enabled where supported.
- Xcode command line tools installed.
- Optional: `ipsw`, `dyld-shared-cache-extractor`, `dylibtree`, Hopper/Ghidra/IDA.

## Baseline capture

```zsh
mkdir -p ~/iflow-lab/baseline
{
  date -u
  sw_vers
  uname -a
  system_profiler SPHardwareDataType | sed -n '1,80p'
} | tee ~/iflow-lab/baseline/system.txt
```

## Feature-state capture

Record manually in `templates/lab_runbook.md`:

- Apple Intelligence enabled/disabled.
- Siri enabled/disabled.
- Shortcuts Use Model availability.
- Network state.
- Language/region.
- Privacy-report duration setting.

## Directory layout

```text
~/iflow-lab/
  baseline/
  inventory/
  dsc-extracted/
  entitlements/
  logs/
  trials/
  manifests/
  pseudo_headers.local/   # local only; do not redistribute
```

## Reproducibility controls

- Run each controlled trial at least twice.
- Keep trial prompts minimal and stable.
- Store log windows with absolute UTC timestamps.
- Record negative findings.
- Avoid mutating system protections or injecting into Apple processes.
