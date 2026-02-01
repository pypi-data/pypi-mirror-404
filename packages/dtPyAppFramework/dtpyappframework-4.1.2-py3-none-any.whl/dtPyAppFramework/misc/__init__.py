import subprocess
import logging
from shlex import quote as shlex_quote


def run_cmd(cmd):
    try:
        # Execute the command, capturing the output and raising an exception if the command fails
        result = subprocess.run(cmd, shell=True, capture_output=True, check=True, encoding="utf-8")

        # Return the stripped standard output
        return result.stdout.strip()
    except Exception as ex:
        # Log the exception and return None
        logging.exception(str(ex))
        return None
