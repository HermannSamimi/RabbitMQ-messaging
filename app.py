import subprocess
import time

# Start both scripts in parallel
p1 = subprocess.Popen(["python3", "producer.py"])
p2 = subprocess.Popen(["python3", "consumer.py"])

# Wait for 60 seconds
time.sleep(60)

# Terminate both
p1.terminate()
p2.terminate()

# Optional: print outputs for debug
out1, err1 = p1.communicate()
out2, err2 = p2.communicate()

print("✅ Producer output:\n", out1.decode() if out1 else "No output")
print("❌ Producer error:\n", err1.decode() if err1 else "No error")
print("✅ Consumer output:\n", out2.decode() if out2 else "No output")
print("❌ Consumer error:\n", err2.decode() if err2 else "No error")