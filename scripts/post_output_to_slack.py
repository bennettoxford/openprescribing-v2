#!/usr/bin/env python3
"""\
Wrapper script for cron jobs which posts log output to a Slack channel.

This follows the traditional cron logic that if the command succeeds AND produces no
output on either stdout or stderr then it does nothing. Otherwise it posts a message.

Note that this takes a single string argument which is the shell command to execute.  If
that command itself involves quoted strings then you will need to use two sets of quotes
or do some form of escaping e.g.

    ./post_output_to_slack.py 'some_command "with quoted argument"'

The Slack channel ID and API token are supplied as environment variables:
SLACK_CHANNEL_ID and SLACK_API_TOKEN.
"""

import argparse
import os
import subprocess
import sys
import traceback

import requests


def main(args, environ):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--task-name", default="Scheduled task")
    parser.add_argument("shell_command")
    parsed = parser.parse_args(args)

    token = environ.get("SLACK_API_TOKEN")
    channel_id = environ.get("SLACK_CHANNEL_ID")
    if not token or not channel_id:
        raise RuntimeError(
            "Environment variables SLACK_API_TOKEN and SLACK_CHANNEL_ID must be set."
        )

    run_command_and_post_output_to_slack(
        token=token, channel_id=channel_id, **vars(parsed)
    )


def run_command_and_post_output_to_slack(
    *, token, channel_id, shell_command, task_name
):
    output, success = run_command(shell_command)
    if output or not success:
        message = format_message(shell_command, task_name, success)
        try:
            post_file_to_slack(token, channel_id, message, output)
        except Exception as exc:
            exc.add_note(f"\nIntended message was:\n{message}\n\n{output}")
            raise


def run_command(shell_command):
    try:
        proc = subprocess.run(
            shell_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except Exception:
        output = traceback.format_exc()
        success = False
    else:
        output = proc.stdout
        success = proc.returncode == 0

    output = output.strip()
    return output, success


def format_message(command, task_name, success):
    emoji = ":white_check_mark:" if success else ":x:"
    status = "succeeded" if success else "failed"
    return f"{task_name} *{status}* {emoji}\n```\n{command}\n```"


def post_file_to_slack(
    token, channel_id, message, contents, filename="output.log", title="Log Output"
):
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}"})

    contents_bytes = contents.encode("utf-8")

    # Get a URL to which to upload file
    response = session.post(
        "https://slack.com/api/files.getUploadURLExternal",
        data={
            "length": len(contents_bytes),
            "filename": filename,
            "snippet_type": "text",
        },
    )
    response.raise_for_status()

    data = response.json()
    if not data.get("ok"):  # pragma: no cover
        raise RuntimeError(f"Slack API error: {data!r}")
    upload_url = data["upload_url"]
    file_id = data["file_id"]

    # Upload the file
    response = session.post(
        upload_url,
        headers={"Content-Type": "application/octet-stream"},
        data=contents_bytes,
    )
    response.raise_for_status()

    # Post a message to the channel with the uploaded file attached
    response = session.post(
        "https://slack.com/api/files.completeUploadExternal",
        json={
            "channel_id": channel_id,
            "initial_comment": message,
            "files": [{"id": file_id, "title": title}],
        },
    )
    response.raise_for_status()

    data = response.json()
    if not data.get("ok"):  # pragma: no cover
        raise RuntimeError(f"Slack API error: {data!r}")


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:], environ=os.environ)
