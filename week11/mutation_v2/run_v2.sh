#!/bin/bash
# Week 11 provisional mutation runs on current master code (6b8884f), mutmut 3.8.0
set -u
cd /home/claude/v2run
. /home/claude/tomlkit/.venv/bin/activate
pip install -q -e . >/dev/null 2>&1
setcfg () {
python3 - "$1" <<'PY'
import sys
dirs=sys.argv[1].split(",")
s=open("pyproject.toml").read()
i=s.index("[tool.mutmut]"); j=s.find("\n[",i+1); j=len(s) if j==-1 else j
lst=", ".join(f'"{d}/"' for d in dirs)
block=f'''[tool.mutmut]
paths_to_mutate = ["tomlkit/"]
tests_dir = [{lst}]
also_copy = [{lst}]
do_not_mutate = ["tomlkit/_compat.py", "tomlkit/_types.py"]
pytest_add_cli_args = ["-p", "no:cacheprovider"]
'''
open("pyproject.toml","w").write(s[:i]+block+s[j:])
PY
}
for run in "ai_only_current:tests_ai" "hybrid_v2:tests_ai,tests_manual,tests_property,tests_tdd,tests_bdd,tests_integration"; do
  name=${run%%:*}; dirs=${run#*:}
  rm -rf mutants; setcfg "$dirs"
  echo "== $name start $(date +%T)"
  ( time timeout 5400 mutmut run --max-children 8 ) > /home/claude/v2out/$name.log 2>&1
  echo "== $name exit $? $(date +%T)"
  mutmut results --all true > /home/claude/v2out/$name.results.txt 2>/dev/null
  awk -F': ' '{print $2}' /home/claude/v2out/$name.results.txt | sort | uniq -c
done
git checkout -q pyproject.toml
echo ALL_DONE
