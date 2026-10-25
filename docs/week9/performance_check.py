import statistics
import time

import tomlkit


SOURCE = """
title = "COMP 441 benchmark"
enabled = true
count = 42
tags = ["testing", "mutation", "bdd"]

[database]
host = "localhost"
port = 5432

[[students]]
name = "Student 1"
score = 75

[[students]]
name = "Student 2"
score = 82
""".lstrip()

OPERATIONS = 5_000
REPEATS = 5


def workload():
    for i in range(OPERATIONS):
        document = tomlkit.parse(SOURCE)
        document["count"] = i
        document["tags"].append("performance")
        rendered = document.as_string()
        reparsed = tomlkit.parse(rendered)

        if reparsed["count"] != i:
            raise AssertionError("Round-trip value mismatch")


durations = []

print("Light-touch tomlkit performance check")
print(f"Operations per repeat: {OPERATIONS}")
print(f"Repeats: {REPEATS}")
print("Workload: parse, modify, serialize, and reparse")

for repeat in range(1, REPEATS + 1):
    start = time.perf_counter()
    workload()
    duration = time.perf_counter() - start
    durations.append(duration)

    rate = OPERATIONS / duration
    print(
        f"Repeat {repeat}: "
        f"{duration:.6f} seconds, "
        f"{rate:.2f} operations/second"
    )

total_operations = OPERATIONS * REPEATS
total_duration = sum(durations)

print(f"Total operations: {total_operations}")
print(f"Total measured time: {total_duration:.6f} seconds")
print(f"Mean repeat time: {statistics.mean(durations):.6f} seconds")
print(f"Median repeat time: {statistics.median(durations):.6f} seconds")
print(f"Minimum repeat time: {min(durations):.6f} seconds")
print(f"Maximum repeat time: {max(durations):.6f} seconds")
print(
    "Overall throughput: "
    f"{total_operations / total_duration:.2f} operations/second"
)
print("Correctness check: all round-trip assertions passed")
