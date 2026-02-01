#!/usr/bin/env python3
"""
Migration script to fix job counter after job ID reuse bug.

This script:
1. Finds the highest existing job ID
2. Creates/updates .job_counter file
3. Clears any stuck jobs in 'queued' status with no PID

Run this if you're experiencing jobs stuck in 'queued' status.
"""

import json
import os
import sys


def fix_job_counter():
    """Fix job counter to prevent ID reuse."""
    # Find souleyez installation root
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    jobs_dir = os.path.join(root, "data", "jobs")
    jobs_file = os.path.join(jobs_dir, "jobs.json")
    counter_file = os.path.join(jobs_dir, ".job_counter")

    if not os.path.exists(jobs_dir):
        print(f"✗ Jobs directory not found: {jobs_dir}")
        return False

    # Read existing jobs
    jobs = []
    if os.path.exists(jobs_file):
        try:
            with open(jobs_file, "r") as f:
                jobs = json.load(f)
        except Exception as e:
            print(f"✗ Error reading jobs file: {e}")
            return False

    # Find max job ID
    max_id = 0
    stuck_jobs = []
    for job in jobs:
        job_id = job.get("id", 0)
        if job_id > max_id:
            max_id = job_id

        # Identify stuck jobs (queued with no PID)
        if job.get("status") == "queued" and job.get("pid") is None:
            stuck_jobs.append(job_id)

    # Create counter file
    next_id = max_id + 1
    try:
        with open(counter_file, "w") as f:
            f.write(str(next_id))
        print(f"✓ Created job counter: next ID will be {next_id}")
    except Exception as e:
        print(f"✗ Error creating counter file: {e}")
        return False

    # Report stuck jobs
    if stuck_jobs:
        print(f"\n⚠️  Found {len(stuck_jobs)} stuck job(s): {stuck_jobs}")
        print("   These jobs are in 'queued' status but have no PID (never started)")
        print(
            "   Recommendation: Delete them with 'souleyez jobs purge' or kill them individually"
        )
    else:
        print("✓ No stuck jobs found")

    print(f"\n✅ Migration complete!")
    print(f"   - Job counter initialized to {next_id}")
    print(f"   - Total jobs in queue: {len(jobs)}")
    print(f"   - Stuck jobs: {len(stuck_jobs)}")

    return True


if __name__ == "__main__":
    success = fix_job_counter()
    sys.exit(0 if success else 1)
