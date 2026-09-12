import random
import subprocess
import time
from datetime import datetime, timedelta, timezone


PYTHON = "/home/ubuntu/twitter_conflicts_api/venv/bin/python3"
FEED_SCRIPT = "/home/ubuntu/twitter_conflicts_api/twitter_conflicts_server/python_script/feed.py"


def random_time_between(start, end):
    """Return a random UTC datetime between start and end."""
    if start > end:
        return None

    seconds = int((end - start).total_seconds())

    if seconds <= 0:
        return start

    return start + timedelta(seconds=random.randint(0, seconds))


def midnight_for(date):
    return datetime.combine(
        date,
        datetime.min.time(),
        tzinfo=timezone.utc
    )


def generate_schedule():
    """
    Generate the remaining runs for today.

    Rules:
      Run 1: 04:00-06:00 UTC
      Run 2: 10:00-18:00 UTC
      Run 3: at least 7h after Run 2, no later than 01:00 next day.

    If a window has already passed, it is skipped rather than
    being executed immediately.
    """

    now = datetime.now(timezone.utc)
    today = now.date()
    midnight = midnight_for(today)

    run1_start = midnight + timedelta(hours=4)
    run1_end = midnight + timedelta(hours=6)

    run2_start = midnight + timedelta(hours=10)
    run2_end = midnight + timedelta(hours=18)

    run3_end = midnight + timedelta(days=1, hours=1)

    schedule = []

    # ---------------------------------------------------------
    # Run 1: 04:00-06:00
    # ---------------------------------------------------------

    if now < run1_end:
        start = max(now, run1_start)

        run1 = random_time_between(start, run1_end)

        if run1 is not None:
            schedule.append(run1)

    # ---------------------------------------------------------
    # Run 2 + Run 3
    # ---------------------------------------------------------

    # If Run 2 window is still available, schedule it.
    if now < run2_end:

        run2_start_actual = max(now, run2_start)

        run2 = random_time_between(
            run2_start_actual,
            run2_end
        )

        if run2 is not None:

            # Run 3 must be at least 7h after Run 2.
            run3_start = run2 + timedelta(hours=7)

            if run3_start <= run3_end:

                run3 = random_time_between(
                    run3_start,
                    run3_end
                )

                schedule.append(run2)
                schedule.append(run3)

    # ---------------------------------------------------------
    # If nothing remains today, generate tomorrow's schedule.
    # ---------------------------------------------------------

    schedule = sorted(
        run_time
        for run_time in schedule
        if run_time > now
    )

    if not schedule:
        tomorrow = today + timedelta(days=1)
        base = midnight_for(tomorrow)

        run1 = random_time_between(
            base + timedelta(hours=4),
            base + timedelta(hours=6)
        )

        run2 = random_time_between(
            base + timedelta(hours=10),
            base + timedelta(hours=18)
        )

        run3_start = run2 + timedelta(hours=7)
        run3_end = base + timedelta(days=1, hours=1)

        run3 = random_time_between(
            run3_start,
            run3_end
        )

        schedule = sorted([run1, run2, run3])

    return schedule


def run_feed():
    now = datetime.now(timezone.utc)

    print(
        f"[{now.isoformat()}] Starting feed.py",
        flush=True
    )

    result = subprocess.run(
        [PYTHON, FEED_SCRIPT]
    )

    print(
        f"[{datetime.now(timezone.utc).isoformat()}] "
        f"feed.py finished with exit code {result.returncode}",
        flush=True
    )


def main():

    while True:

        schedule = generate_schedule()

        print(
            "\nGenerated schedule (UTC):",
            flush=True
        )

        for i, run_time in enumerate(schedule, 1):
            print(
                f"  Run {i}: "
                f"{run_time.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                flush=True
            )

        for run_time in schedule:

            while True:

                now = datetime.now(timezone.utc)
                delay = (run_time - now).total_seconds()

                if delay <= 0:
                    break

                time.sleep(min(delay, 60))

            run_feed()

        # After completing the schedule, wait until midnight.
        now = datetime.now(timezone.utc)

        tomorrow = now.date() + timedelta(days=1)
        next_midnight = midnight_for(tomorrow)

        print(
            f"[{now.isoformat()}] "
            f"All scheduled runs completed. "
            f"Waiting until {next_midnight.isoformat()}",
            flush=True
        )

        while True:

            now = datetime.now(timezone.utc)

            if now >= next_midnight:
                break

            delay = (next_midnight - now).total_seconds()

            time.sleep(min(delay, 60))


if __name__ == "__main__":
    main()
