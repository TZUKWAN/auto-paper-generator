import subprocess
import sys

result = subprocess.run(
    [sys.executable, "test_both_models.py"],
    capture_output=True,
    text=True,
    cwd=r"D:\自动化商业计划书脚本\自动化论文脚本"
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")
