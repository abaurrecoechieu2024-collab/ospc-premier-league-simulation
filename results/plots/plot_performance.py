import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

with open("results/array/baseline-100k/timing.csv") as f:
    baseline = next(csv.DictReader(f))

with open("results/array/job-30256/timing_all_tasks.csv") as f:
    tasks = list(csv.DictReader(f))

baseline_time = float(baseline["simulation_seconds"])
parallel_times = [float(t["simulation_seconds"]) for t in tasks]

labels = ["Baseline"] + [f"Task {i}" for i in range(4)]
times = [baseline_time] + parallel_times

plt.figure(figsize=(9, 5))
bars = plt.bar(labels, times)

plt.ylabel("Simulation time (seconds)")
plt.title("Premier League Simulation - Execution Times")

for bar, value in zip(bars, times):
    plt.text(bar.get_x() + bar.get_width()/2,
             value + 0.08, f"{value:.2f}s", ha="center")

plt.ylim(0, max(times) * 1.2)
plt.tight_layout()
plt.savefig("results/plots/performance.png", dpi=200)
plt.close()

print("Graph saved to results/plots/performance.png")
