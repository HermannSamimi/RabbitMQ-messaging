
import subprocess
import time

p1 = subprocess.Popen(["python3", "producer.py"])
p2 = subprocess.Popen(["python3", "consumer.py"])

time.sleep(60)  # run for 1 minute
p1.terminate()
p2.terminate()