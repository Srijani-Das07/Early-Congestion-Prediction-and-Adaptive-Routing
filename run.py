import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def run(file, desc):
    print(f"\n{'='*55}")
    print(f"  {desc}")
    print(f"{'='*55}")
    result = subprocess.run([sys.executable, file], capture_output=False)
    if result.returncode != 0:
        print(f"\n❌ {file} failed. Fix errors above before continuing.")
        sys.exit(1)
    print(f"✅ {file} completed successfully.")

print("\n" + "-"*55)
print("  CN PROJECT — Full Pipeline Runner")
print("-"*55)
print("Running all files in order...\n")

run("network_setup.py",      "Step 1/5 — Building the Network")
run("congestion_monitor.py", "Step 2/5 — Testing Congestion Monitor")
run("adaptive_routing.py",   "Step 3/5 — Testing Adaptive Routing")
run("simulation.py",         "Step 4/5 — Running Simulation")
run("visualize.py",          "Step 5/5 — Generating Charts")

print("\n" + "-"*55)
print("  ALL STEPS COMPLETE!")
print("  Check results.png in this folder for charts.")
print("-"*55 + "\n")