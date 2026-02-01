# subprocess_utils.py Documentation

## Overview
Subprocess utilities module that handles Windows/Linux differences for subprocess operations, providing cross-platform process management, command execution, and output capture.


## Functions

### `get_child_pids_linux(parent_pid, include_parent=True, recursive=True)`
Returns list of all child process IDs on Linux systems.
- **Parameters:**
  - `parent_pid`: Parent process ID to find children of
  - `include_parent`: Include parent PID in result (default: True)
  - `recursive`: Find all descendants, not just direct children (default: True)
- **Returns:** List of integer PIDs
- **Note:** Linux-specific, uses `ps` command

### `popen(command, pipe_output=True)`
Creates subprocess.Popen object with OS-appropriate settings.
- **Parameters:**
  - `command`: Command to execute (str or list)
  - `pipe_output`: Capture stdout/stderr to PIPE (default: True)
- **Returns:** subprocess.Popen object
- **Platform Differences:**
  - Windows: Uses shell=True
  - Linux: Uses shell=True with preexec_fn=os.setsid for process group management
- **Security Note:** Commands must be properly vetted before execution

### `get_command_output(command, encoding="utf-8")`
Runs command to completion and returns output as CompletedProcess.
- **Parameters:**
  - `command`: Command to execute (str)
  - `encoding`: Output encoding (default: "utf-8", None for bytes)
- **Returns:** subprocess.CompletedProcess with stdout/stderr as strings
- **Security Note:** Commands must be properly vetted before execution

### `get_command_output_as_string(command, encoding="utf-8")`
Runs command to completion and returns stdout as string.
- **Parameters:**
  - `command`: Command to execute (str)
  - `encoding`: Output encoding (default: "utf-8")
- **Returns:** String containing command stdout
- **Security Note:** Commands must be properly vetted before execution

### `kill_proc(proc, forcefully=False)`
Attempts to terminate a subprocess.
- **Parameters:**
  - `proc`: subprocess.Popen object to kill
  - `forcefully`: Force kill (not yet implemented)
- **Returns:** bool - True if successful
- **Platform Differences:**
  - Windows: Uses os.kill with SIGTERM
  - Linux: Uses os.killpg to kill process group

### `proc_still_running(proc)`
Checks if a subprocess is still running.
- **Parameters:**
  - `proc`: subprocess.Popen object to check
- **Returns:** bool - True if process is running

## Classes

### `SubProcessPopenObject`
Cross-platform wrapper for long-running subprocess management.

#### Constructor
```python
SubProcessPopenObject(command, pipe_output=True, verbose=True)
```
- **Parameters:**
  - `command`: Command to execute (str or list)
  - `pipe_output`: Capture output (default: True)
  - `verbose`: Enable logging (default: True)

#### Attributes
- `pipe_output`: Whether output is being captured
- `running`: Process running status
- `verbose`: Logging enabled flag
- `exit_code`: Process exit code (None while running)
- `stdout`: Captured stdout text
- `stderr`: Captured stderr text
- `command`: Original command
- `spp_obj`: Underlying Popen object

#### Methods

##### `terminate(forcefully=False)`
Attempts to kill the subprocess.
- **Parameters:**
  - `forcefully`: Force termination (not implemented)
- **Returns:** bool - Success status

##### `check_process()`
Checks process status and captures available output.
- **Returns:** bool - True if still running
- **Behavior:**
  - Attempts to read stdout/stderr with 1-second timeout
  - Updates `running`, `exit_code`, `stdout`, and `stderr` attributes
  - Logs status if verbose mode enabled

## Usage Examples

```python
from subprocess_utils import get_command_output, SubProcessPopenObject
import time

# Simple command execution
result = get_command_output("ls -la")
print(result.stdout)

# Get just stdout as string
output = get_command_output_as_string("echo 'Hello World'")
print(output)  # "Hello World\n"

# Long-running process management
proc = SubProcessPopenObject("python long_script.py")
while proc.running:
    proc.check_process()
    print("Process still running...")
    time.sleep(5)

print(f"Exit code: {proc.exit_code}")
print(f"Output: {proc.stdout}")
print(f"Errors: {proc.stderr}")

# Check if process is running
from subprocess_utils import popen, proc_still_running
p = popen("sleep 10")
if proc_still_running(p):
    print("Process is running")
```

## Notes

- **Windows Output Capture:** Grabbing output on Windows can be tricky. For long-running processes, consider using .bat files that log output to files.
- **Security:** All command execution functions require properly vetted commands to prevent injection attacks.
- **Cross-Platform:** Module automatically detects OS and adjusts behavior accordingly.
- **Process Groups:** On Linux, processes are created in new sessions for better control over child processes.
