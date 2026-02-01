
import subprocess
import sys
import os
from pathlib import Path

def create_scheduled_task(time_str: str, source_dir: str):
    """
    Create a daily scheduled task using Windows Task Scheduler.
    
    Args:
        time_str (str): Time in HH:MM format (24-hour).
        source_dir (str): The source directory to organize.
        
    Returns:
        tuple: (success (bool), message (str))
    """
    task_name = "SFOFileOrganizer_Auto"
    
    # Determine what to run (the script or the exe)
    if getattr(sys, 'frozen', False):
        # Running as executable
        exe_path = sys.executable
        # Wrap in quotes
        command = f'"{exe_path}" --source "{source_dir}" --no-log-file'
    else:
        # Running as script
        python_exe = sys.executable
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "organizer.py")
        command = f'"{python_exe}" "{script_path}" --source "{source_dir}" --no-log-file'

    # Build schtasks command
    # /F forces creation (overwrites if exists)
    # /RL HIGHEST ensures it runs with permissions if needed (optional, but good for file ops)
    sch_cmd = [
        "schtasks", "/create",
        "/tn", task_name,
        "/tr", command,
        "/sc", "daily",
        "/st", time_str,
        "/f"
    ]
    
    try:
        # Create startup info to hide the console window if possible
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        result = subprocess.run(
            sch_cmd, 
            capture_output=True, 
            text=True, 
            startupinfo=startupinfo
        )
        
        if result.returncode == 0:
            return True, f"Task scheduled daily at {time_str}"
        else:
            return False, f"Failed to schedule: {result.stderr.strip()}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def delete_scheduled_task():
    """Remove the scheduled task."""
    task_name = "SFOFileOrganizer_Auto"
    try:
        subprocess.run(
            ["schtasks", "/delete", "/tn", task_name, "/f"],
            capture_output=True,
            startupinfo=subprocess.STARTUPINFO()
        )
        return True, "Task removed"
    except:
        return False, "Could not remove task"
