"""
Scheduler tool for dynamic job scheduling via Luigi,
with a persistent on-disk registry and a listing tool.
"""
import sys

os_platform = sys.platform

import time
import subprocess
import json
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from langchain_core.runnables import RunnableConfig
from agentfoundry.agents.tools import get_config_param
from langchain_core.tools import tool

if os_platform == 'win32':
    import luigi
    # where we record every schedule call
    JOB_STORE_FILE = "scheduled_jobs.json"


    def _load_job_store() -> List[Dict]:
        try:
            with open(JOB_STORE_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []


    def _save_job_store(jobs: List[Dict]):
        with open(JOB_STORE_FILE, "w") as f:
            json.dump(jobs, f, indent=2, sort_keys=True)


    def _record_job(entry: Dict):
        jobs = _load_job_store()
        jobs.append(entry)
        _save_job_store(jobs)


    class OneTimeTask(luigi.Task):
        job_id = luigi.Parameter()
        run_at = luigi.Parameter()  # ISO timestamp
        command = luigi.Parameter()

        def run(self):
            scheduled = datetime.fromisoformat(self.run_at)
            now = datetime.now()
            if scheduled > now:
                time.sleep((scheduled - now).total_seconds())
            subprocess.run(self.command, shell=True, check=True)


    class RecurringBatchTask(luigi.WrapperTask):
        job_id = luigi.Parameter()
        start_time = luigi.Parameter()  # ISO timestamp
        interval = luigi.Parameter()  # "daily" or "weekly"
        command = luigi.Parameter()
        count = luigi.IntParameter(default=1)
        end_time = luigi.Parameter(default=None)

        def requires(self):
            times = []
            current = datetime.fromisoformat(self.start_time)

            for _ in range(self.count):
                times.append(current)
                if self.interval == "daily":
                    current += timedelta(days=1)
                elif self.interval == "weekly":
                    current += timedelta(weeks=1)
                else:
                    raise ValueError(f"Unsupported interval: {self.interval}")

                if self.end_time:
                    stop = datetime.fromisoformat(self.end_time)
                    if current > stop:
                        break

            for t in times:
                yield OneTimeTask(
                    job_id=self.job_id,
                    run_at=t.isoformat(),
                    command=self.command
                )


    @tool
    def schedule_one_time_job(job_id: str, run_at: str, command: str, config: RunnableConfig) -> str:
        """
        Schedule a one-time job to run a shell command at the specified ISO datetime. If the command is to schedule an
        AI agent action, then the command must contain 'python run_orchestrator.py --prompt "TASK TO EXECUTE"'
        The function expects following args:
            job_id: str
            run_at: str containing ISO datetime of execution
            command: str command to run
            config: RunnableConfig
        """
        user_id = get_config_param(config, "user_id")
        org_id = get_config_param(config, "org_id")
        sec_level = get_config_param(config, "security_level")
        llm_type = get_config_param(config, "llm")

        if "run_orchestrator" in command:
            command += f" --user-id {user_id} --org-id {org_id} --security-level {sec_level} --llm-type {llm_type}"

        # kick off the Luigi task
        def _async_run():
            luigi.build([OneTimeTask(job_id=job_id, run_at=run_at, command=command)], local_scheduler=True)
        threading.Thread(target=_async_run, daemon=True).start()
        # record it for later listing
        _record_job({
            "type": "one-time",
            "job_id": job_id,
            "run_at": run_at,
            "command": command,
        })

        return f"Scheduled one-time job '{job_id}' at {run_at}"


    @tool
    def schedule_recurring_job(
            job_id: str,
            start_time: str,
            interval: str,
            command: str,
            config: RunnableConfig,
            count: int = 1,
            end_time: Optional[str] = None
    ) -> str:
        """
        Schedule a recurring job to run a shell command. If the command is to schedule an AI agent action, then the command
        must contain 'python run_orchestrator.py --prompt "TASK TO EXECUTE"'
          - start_time: ISO datetime for first run
          - interval: 'daily' or 'weekly'
          - count: how many times to run
          - end_time: optional ISO datetime to stop early
        """
        user_id = get_config_param(config, "user_id")
        org_id = get_config_param(config, "org_id")
        sec_level = get_config_param(config, "security_level")
        llm_type = get_config_param(config, "llm")

        if "run_orchestrator" in command:
            command += f" --user-id {user_id} --org-id {org_id} --security-level {sec_level} --llm-type {llm_type}"

        def _async_run():
            luigi.build([
                RecurringBatchTask(
                    job_id=job_id,
                    start_time=start_time,
                    interval=interval,
                    command=command,
                    count=count,
                    end_time=end_time or None,
                )
            ], local_scheduler=True)

        threading.Thread(target=_async_run, daemon=True).start()

        # record it for later listing
        _record_job({
            "type": "recurring",
            "job_id": job_id,
            "start_time": start_time,
            "interval": interval,
            "count": count,
            "end_time": end_time,
            "command": command,
        })

        return (
            f"Scheduled recurring job '{job_id}' every {interval} "
            f"starting at {start_time} for {count} occurrence(s)"
        )


    @tool
    def list_scheduled_jobs() -> str:
        """
        List all jobs that have been scheduled so far.
        """
        jobs = _load_job_store()
        if not jobs:
            return "No jobs scheduled yet."

        lines = []
        for j in jobs:
            if j["type"] == "one-time":
                lines.append(f"[one-time] '{j['job_id']}' at {j['run_at']} -> {j['command']}")
            else:
                end = j.get("end_time") or "N/A"
                lines.append(
                    f"[recurring] '{j['job_id']}' every {j['interval']}, "
                    f"start {j['start_time']}, count {j['count']}, "
                    f"end {end} -> {j['command']}"
                )
        return "\n".join(lines)
else:
    import shlex
    import subprocess
    from datetime import datetime
    from typing import Optional
    from zoneinfo import ZoneInfo                 # Python 3.9+

    from langchain_core.tools import tool
    from agentfoundry.registry.tool_registry import ToolRegistry
    try:
        from crontab import CronTab  # type: ignore  # pip install python-crontab
    except Exception:  # pragma: no cover
        CronTab = None

    # prefix all cron comments so we can identify our entries later
    JOB_COMMENT_PREFIX = "agentfoundry:"
    # assume user provides times in Eastern Time (ET)
    LOCAL_TZ = ZoneInfo("America/New_York")

    @tool
    def schedule_one_time_job(job_id: str, run_at: str, command: str) -> str:
        """
        Schedule a one-time shell command via `at`.
          - run_at: ISO datetime in local ET (e.g. "2025-07-30T14:30:00")
          - command: the shell command to run

        Converts run_at from ET to UTC for the `at` scheduler.
        """
        # parse local time and convert to UTC
        if CronTab is None:
            return (
                "python-crontab is not installed. Install with 'pip install python-crontab' "
                "to enable scheduling on this platform."
            )
        dt_local = datetime.fromisoformat(run_at).replace(tzinfo=LOCAL_TZ)
        dt_utc = dt_local.astimezone(ZoneInfo("UTC"))
        # at accepts formats like "HH:MM YYYY-MM-DD"
        at_time = dt_utc.strftime("%H:%M %Y-%m-%d")

        # embed job_id comment in the at job payload
        at_input = f"# {JOB_COMMENT_PREFIX}{job_id}\n/bin/bash -lc {shlex.quote(command)}\n"
        proc = subprocess.run(
            ["at", at_time],
            input=at_input,
            text=True,
            capture_output=True
        )
        if proc.returncode != 0:
            err = proc.stderr.strip() or proc.stdout.strip()
            raise RuntimeError(f"at scheduling failed: {err}")
        return f"Scheduled one-time job '{job_id}' at local {run_at} (UTC {dt_utc.isoformat()}) via at"

    @tool
    def schedule_recurring_job(
        job_id: str,
        minute: Optional[int] = None,
        hour: Optional[int] = None,
        day_of_month: Optional[str] = "*",
        month: Optional[str] = "*",
        day_of_week: Optional[str] = "*",
        command: str = "",
    ) -> str:
        """
        Schedule a recurring cron job.
          - minute, hour: integers 0–59 / 0–23 in local ET (required)
          - day_of_month, month, day_of_week: cron fields (default '*')
          - command: shell command to run

        Converts local ET schedule to UTC when writing to crontab.
        """
        if minute is None or hour is None:
            raise ValueError("Must specify both minute and hour for a cron job in local time")

        # convert today's local schedule to UTC to get correct hour/minute
        now_local = datetime.now(LOCAL_TZ)
        dt_local = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        dt_utc = dt_local.astimezone(ZoneInfo("UTC"))
        utc_minute = dt_utc.minute
        utc_hour = dt_utc.hour

        cron = CronTab(user=True)
        job = cron.new(
            command=f"/bin/bash -lc {shlex.quote(command)}",
            comment=JOB_COMMENT_PREFIX + job_id
        )
        if CronTab is None:
            return (
                "python-crontab is not installed. Install with 'pip install python-crontab' "
                "to enable scheduling on this platform."
            )
        # schedule at UTC fields; days remain as provided
        job.setall(f"{utc_minute} {utc_hour} {day_of_month} {month} {day_of_week}")
        job.enable()
        cron.write()

        return (
            f"Scheduled recurring cron job '{job_id}' at local {hour:02d}:{minute:02d} ET "
            f"(UTC {utc_hour:02d}:{utc_minute:02d}) every {day_of_week}/{day_of_month}/{month}"
        )

    @tool
    def list_scheduled_jobs() -> str:
        """
        List all one-time (at) and recurring (cron) jobs created by agentfoundry.
        """
        lines = []

        # one-time via atq
        atq = subprocess.run(["atq"], capture_output=True, text=True)
        if atq.stdout.strip():
            lines.append("One-time jobs (at):")
            for entry in atq.stdout.strip().splitlines():
                lines.append("  " + entry)
        else:
            lines.append("No one-time jobs in at-queue.")

        # recurring via cron
        if CronTab is None:
            return "python-crontab not installed."
        cron = CronTab(user=True)
        cron_jobs = [j for j in cron if j.comment and j.comment.startswith(JOB_COMMENT_PREFIX)]
        if cron_jobs:
            lines.append("\nRecurring cron jobs:")
            for j in cron_jobs:
                job_id = j.comment[len(JOB_COMMENT_PREFIX):]
                lines.append(f"  [{job_id}] {j.slices} → {j.command}")
        else:
            lines.append("\nNo recurring cron jobs found.")

        return "\n".join(lines)

    @tool
    def delete_scheduled_job(job_id: str) -> str:
        """
        Delete both one-time and recurring jobs matching the given job_id.
        """
        deleted = []
        # 1. Remove at jobs whose payload contains our job_id comment
        atq = subprocess.run(["atq"], capture_output=True, text=True)
        for line in atq.stdout.strip().splitlines():
            job_num = line.split()[0]
            payload = subprocess.run(["at", "-c", job_num], capture_output=True, text=True).stdout
            if f"# {JOB_COMMENT_PREFIX}{job_id}" in payload:
                subprocess.run(["atrm", job_num], check=False)
                deleted.append(f"at job {job_num}")

        # 2. Remove cron jobs tagged with our comment
        if CronTab is None:
            return "python-crontab not installed."
        cron = CronTab(user=True)
        cron_jobs = [j for j in cron if j.comment == JOB_COMMENT_PREFIX + job_id]
        for j in cron_jobs:
            cron.remove(j)
            deleted.append(f"cron job '{job_id}'")
        cron.write()

        if not deleted:
            return f"No scheduled jobs found with job_id '{job_id}'"
        return "Deleted: " + ", ".join(deleted)


# def register(registry: ToolRegistry):
#     registry.register_tool(schedule_one_time_job)
#     registry.register_tool(schedule_recurring_job)
#     registry.register_tool(list_scheduled_jobs)
