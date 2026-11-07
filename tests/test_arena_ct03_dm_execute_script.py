"""Replay the exact ten-run shell with local fake Docker, NEVER real OMC."""
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from scripts.arena_cafe.ct03_dm_initial_batch import prepare
from scripts.arena_cafe.ct03_m_prepare import prepare as prepare_m
from test_arena_ct03_dm_initial_batch import reuse_fixture

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/arena_cafe/ct03_dm_execute_ten_once.sh"

MOCK=String=None
DOCKER_FAKE=r'''#!/usr/bin/env python3
import csv,json,re,sys,os
from pathlib import Path
script=Path(sys.argv[-1])
match=re.search(r"([DM])([1-5])\.mos$",script.name)
if not match:raise SystemExit("wrong original D/M script")
arm,idx=match.group(1),int(match.group(2))
root=Path("artifacts/ct03-producer/dm-ten")
candidate=json.loads((root/arm/"manifest.json").read_text())["candidates"][idx]
model=(candidate["name"] if arm=="D" else "ArenaCT03M."+candidate["class_name"])
prefix=arm.lower()+str(idx).zfill(2)
trace=root/arm/(prefix+"_res.csv")
if arm=="D":
  n=len(candidate["structure"]["stocks"])
  header=["time","delivered","lost"]+["s"+str(i) for i in range(1,n+1)]
else:
  stocks=[x["id"]+".waiting" for x in candidate["original_ast"]["instances"]
          if x["role"] in ("preparation","dispatch","transit")]
  header=["time","deliveredTotal",*stocks]
with trace.open("w",newline="") as f:
  w=csv.writer(f);w.writerow(header)
  for step in range(65):
    t=step/8
    y=.1*t
    m=1.7*min(t,2)
    failed=os.environ.get("MOCK_BAD_CANDIDATE")==arm+str(idx)
    remaining=0 if failed else m-y
    if arm=="D":w.writerow([t,y,0,remaining]+[0]*(n-1))
    else:w.writerow([t,y,remaining]+[0]*(len(stocks)-1))
print("OpenModelica 1.26.5 SYNTHETIC_TEST_DO_NOT_CITE")
print("Check of "+model+" completed successfully.")
print("resultFile = /repo/"+str(trace))
print("LOG_SUCCESS SYNTHETIC_NOT_OMC")
'''


class TenOMCShellNoProvider(unittest.TestCase):
    def test_bash_valid_and_denies_unauthorized_default(self):
        parsed=subprocess.run(["bash","-n",str(SCRIPT)],text=True,
                              capture_output=True,timeout=10)
        self.assertEqual(parsed.returncode,0,parsed.stderr)
        blocked=subprocess.run(["bash",str(SCRIPT)],cwd=ROOT,
                               capture_output=True,text=True,
                               env={"PATH":os.environ["PATH"]},timeout=10)
        self.assertNotEqual(blocked.returncode,0)
        self.assertIn("CT03_DM_MANUAL_AUTH_FROZEN_SHA_WORLD_BUDGET_GATE",
                      blocked.stderr)

    def test_real_bash_mock_docker_ten_routes_one_failure_preserved_no_retry(self):
        oldcwd=Path.cwd()
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            try:
                os.chdir(root)
                reuse=reuse_fixture()
                m=prepare_m(Path("expected-m"))
                reuse["items"][1]["model_sha256"]=m["native_modelica_sha256"]
                out=Path("artifacts/ct03-producer/dm-ten")
                p=prepare(out,reuse)
                self.assertEqual(len(p["rows"]),10)
            finally:
                os.chdir(oldcwd)
            bindir=root/"bin";bindir.mkdir()
            exe=bindir/"docker";exe.write_text(DOCKER_FAKE)
            exe.chmod(0o755)
            runtmp=root/"runner-temp"
            for x in ("e1-libs/msl","e1-libs/systemdynamics","e1-home"):
                (runtmp/x).mkdir(parents=True)
            env={**os.environ,
                 "PATH":str(bindir)+os.pathsep+os.environ["PATH"],
                 "PYTHONPATH":str(ROOT),
                 "RUNNER_TEMP":str(runtmp),
                 "GITHUB_EVENT_NAME":"workflow_dispatch",
                 "GITHUB_RUN_ATTEMPT":"1",
                 "GITHUB_REF":"refs/heads/experiment/arena-ct00-ct02-20261107",
                 "GITHUB_SHA":"a"*40,
                 "GITHUB_RUN_ID":"99999999",
                 "CT03_FROZEN_SHA":"a"*40,
                 "CT03_LIVE_BATCH_AUTH":"CT03_ONE_APPROVED_LOT",
                 "CT03_DM_TEN_AUTH":"EXACTLY_TEN_ORIGINAL_INITIALS",
                 "CT03_OMC_BUDGET_MAX":"19",
                 "CT03_OMC_WORLD_ATTEMPTS":"1",
                 "MOCK_BAD_CANDIDATE":"M3"}
            run=subprocess.run(["bash",str(SCRIPT)],cwd=root,env=env,
                               capture_output=True,text=True,timeout=150)
            self.assertEqual(run.returncode,0,run.stderr[-4000:])
            out=root/"artifacts/ct03-producer/dm-ten"
            attempts=(out/"attempts.log").read_text().splitlines()
            self.assertEqual(len(attempts),10)
            self.assertEqual([r.split(" attempted")[0] for r in attempts],
                             [f"{a}{i}" for a in "DM" for i in (1,2,3,4,5)])
            summary=json.loads((out/"attempts-summary.json").read_text())
            self.assertEqual(summary["attempts"],10)
            self.assertEqual(summary["failed_routes"],1)
            self.assertEqual(summary["retry_count"],0)
            fail=json.loads((out/"M/m03-result.json").read_text())
            self.assertEqual(fail["status"],"G2_FAILED_NATIVE_ATTEMPT_NO_FORECAST")
            self.assertIsNone(fail["forecast"])
            self.assertEqual(fail["failure_class"],"G2_CHECK_FAILED")
            for arm in "DM":
                for index in range(1,6):
                    code=f"{arm.lower()}{index:02d}"
                    self.assertTrue((out/arm/(code+"-omc.log")).exists())
                    self.assertTrue((out/arm/(code+"-result.json")).exists())
                    if arm=="M" and index==3:continue
                    result=json.loads((out/arm/(code+"-result.json")).read_text())
                    self.assertEqual(result["status"],
                        "ONE_REAL_ORIGINAL_INITIAL_NATIVE_CHECKED_NOT_SCORED")
                    self.assertEqual([x["time"] for x in result["forecast"]],[6,8])
            self.assertFalse((root/"artifacts/ct03-producer/B").exists())
            self.assertFalse((root/"artifacts/ct03-producer/lock.json").exists())


if __name__=="__main__":
    unittest.main()
