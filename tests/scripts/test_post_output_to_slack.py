import textwrap
import unittest

import pytest
import responses

from scripts import post_output_to_slack


def test_main(monkeypatch):
    mock_post = unittest.mock.Mock()
    monkeypatch.setattr(post_output_to_slack, "post_file_to_slack", mock_post)
    post_output_to_slack.main(
        ["--task-name", "Test Task", "echo foo"],
        {
            "SLACK_API_TOKEN": "token",
            "SLACK_CHANNEL_ID": "channel_id",
        },
    )
    mock_post.assert_called_with(
        "token",
        "channel_id",
        textwrap.dedent(
            """\
            Test Task *succeeded* :white_check_mark:
            ```
            echo foo
            ```"""
        ),
        "foo",
    )


def test_main_success_no_output(monkeypatch):
    mock_post = unittest.mock.Mock()
    monkeypatch.setattr(post_output_to_slack, "post_file_to_slack", mock_post)
    post_output_to_slack.main(
        ["true"],
        {"SLACK_API_TOKEN": "t", "SLACK_CHANNEL_ID": "c"},
    )
    mock_post.assert_not_called()


def test_main_failed_no_output(monkeypatch):
    mock_post = unittest.mock.Mock()
    monkeypatch.setattr(post_output_to_slack, "post_file_to_slack", mock_post)
    post_output_to_slack.main(
        ["--task-name", "Test Task", "false"],
        {
            "SLACK_API_TOKEN": "token",
            "SLACK_CHANNEL_ID": "channel_id",
        },
    )
    mock_post.assert_called_with(
        "token",
        "channel_id",
        textwrap.dedent(
            """\
            Test Task *failed* :x:
            ```
            false
            ```"""
        ),
        "",
    )


def test_main_exception(monkeypatch):
    def subprocess_run_with_exc(*args, **kwargs):
        raise RuntimeError("something went wrong")

    monkeypatch.setattr(post_output_to_slack.subprocess, "run", subprocess_run_with_exc)
    mock_post = unittest.mock.Mock()
    monkeypatch.setattr(post_output_to_slack, "post_file_to_slack", mock_post)
    post_output_to_slack.main(
        ["--task-name", "Test Task", "echo foo"],
        {
            "SLACK_API_TOKEN": "token",
            "SLACK_CHANNEL_ID": "channel_id",
        },
    )
    mock_post.assert_called_with(
        "token",
        "channel_id",
        textwrap.dedent(
            """\
            Test Task *failed* :x:
            ```
            echo foo
            ```"""
        ),
        unittest.mock.ANY,
    )
    contents = mock_post.call_args.args[-1]

    assert "Traceback" in contents
    assert "RuntimeError" in contents


def test_main_missing_env_vars():
    with pytest.raises(RuntimeError, match="Environment variables"):
        post_output_to_slack.main(
            ["--task-name", "Test Task", "echo foo"],
            {},
        )


@responses.activate
def test_post_file_to_slack():
    responses.post(
        "https://slack.com/api/files.getUploadURLExternal",
        json={
            "ok": True,
            "upload_url": "https://files.slack.com/upload",
            "file_id": "abc123",
        },
    )
    responses.post(
        "https://files.slack.com/upload",
        body="OK",
    )
    responses.post(
        "https://slack.com/api/files.completeUploadExternal",
        json={
            "ok": True,
        },
    )
    post_output_to_slack.post_file_to_slack(
        "token",
        "channel_id",
        "hello there",
        "file contents here",
    )


def test_main_post_to_slack_failed(monkeypatch):
    mock_post = unittest.mock.Mock(side_effect=RuntimeError("Slack is down"))
    monkeypatch.setattr(post_output_to_slack, "post_file_to_slack", mock_post)
    with pytest.raises(
        RuntimeError,
        # Message should include the Slack exception, the original command and the
        # command output
        match=r"""(?sx)
        Slack\ is\ down
        .*
        echo\ 'foo'\ 'bar'
        .*
        foo\ bar
        """,
    ):
        post_output_to_slack.main(
            ["echo 'foo' 'bar'"],
            {"SLACK_API_TOKEN": "token", "SLACK_CHANNEL_ID": "channel_id"},
        )
