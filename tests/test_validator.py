import copy, importlib.util, json, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("validator",ROOT/"scripts/check_project.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class ValidatorTests(unittest.TestCase):
 def setUp(self): self.plan=json.loads((ROOT/"assets/storyboard.example.json").read_text())
 def check(self, plan):
  c=m.Check(plan,ROOT/"assets");c.plan();return c
 def test_template(self): self.assertEqual(self.check(self.plan).errors,[])
 def test_invalid_duration(self):
  self.plan["duration"]=-1;self.assertTrue(self.check(self.plan).errors)
 def test_missing_shots(self):
  self.plan["shots"]=[];self.assertTrue(self.check(self.plan).errors)
 def test_odd_width(self):
  self.plan["width"]=101;self.assertTrue(self.check(self.plan).errors)
 def test_plan_cli(self):
  r=subprocess.run([sys.executable,str(ROOT/"scripts/check_project.py"),str(ROOT/"assets/storyboard.example.json"),"--plan-only"],capture_output=True,text=True)
  self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_bad_option_combination(self):
  r=subprocess.run([sys.executable,str(ROOT/"scripts/check_project.py"),str(ROOT/"assets/storyboard.example.json"),"--decode"],capture_output=True,text=True)
  self.assertEqual(r.returncode,2)
if __name__=="__main__":unittest.main()
