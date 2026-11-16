"""Create and remove the user's daily Windows synchronization task."""

from datetime import datetime
import subprocess


TASK_NAME = "StudIPSync Daily"


def _powershell_literal(value):
    return "'" + value.replace("'", "''") + "'"


def create_task_script(schedule_time, executable, script=None):
    """Build a PowerShell script for a daily, interactive-user task."""
    try:
        parsed_time = datetime.strptime(schedule_time, "%H:%M")
    except ValueError as error:
        raise ValueError("Bitte eine Uhrzeit im Format HH:MM eingeben.") from error
    if parsed_time.strftime("%H:%M") != schedule_time:
        raise ValueError("Bitte eine Uhrzeit im Format HH:MM eingeben.")

    arguments = f'"{script}" --sync' if script else "--sync"
    return "\n".join(
        [
            "$ErrorActionPreference = 'Stop'",
            f"$action = New-ScheduledTaskAction -Execute {_powershell_literal(executable)} "
            f"-Argument {_powershell_literal(arguments)}",
            f"$trigger = New-ScheduledTaskTrigger -Daily -At {_powershell_literal(schedule_time)}",
            "$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun "
            "-AllowStartIfOnBatteries -DontStopIfGoingOnBatteries",
            '$principal = New-ScheduledTaskPrincipal '
            '-UserId "$env:USERDOMAIN\\$env:USERNAME" '
            '-LogonType Interactive -RunLevel Limited',
            f"Register-ScheduledTask -TaskName {_powershell_literal(TASK_NAME)} "
            "-Action $action -Trigger $trigger -Settings $settings "
            "-Principal $principal -Force | Out-Null",
        ]
    )


def _run_powershell(script):
    return subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def create_daily_task(schedule_time, executable, script=None):
    """Register or replace the daily task for the current Windows user."""
    _run_powershell(create_task_script(schedule_time, executable, script))


def daily_task_is_enabled():
    """Return whether the daily synchronization task is enabled."""
    task_name = _powershell_literal(TASK_NAME)
    result = _run_powershell(
        "$ErrorActionPreference = 'Stop'\n"
        f"$task = Get-ScheduledTask -TaskName {task_name} -ErrorAction SilentlyContinue\n"
        "if ($task -and $task.State -ne 'Disabled') { 'true' } else { 'false' }"
    )
    return result.stdout.strip().lower() == "true"


def delete_daily_task():
    """Remove the daily task if it exists."""
    task_name = _powershell_literal(TASK_NAME)
    _run_powershell(
        "$ErrorActionPreference = 'Stop'\n"
        f"$task = Get-ScheduledTask -TaskName {task_name} -ErrorAction SilentlyContinue\n"
        f"if ($task) {{ Unregister-ScheduledTask -TaskName {task_name} -Confirm:$false }}"
    )
