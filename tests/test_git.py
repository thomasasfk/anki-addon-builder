import pytest
from unittest.mock import patch
from pathlib import Path
from aab.git import Git


@pytest.fixture
def git():
    return Git()


@pytest.mark.parametrize(
    "path, version, expected_cmd", [
        pytest.param(
            "C:\\Users\\test\\addon",
            "1.0.0",
            'git archive --format tar 1.0.0 | tar -x -C "C:/Users/test/addon"',
            id="windows_path_release"
        ),
        pytest.param(
            "/home/user/addon",
            "1.0.0",
            'git archive --format tar 1.0.0 | tar -x -C "/home/user/addon"',
            id="unix_path"
        ),
        pytest.param(
            "C:\\Program Files\\My Addon",
            "1.0.0",
            'git archive --format tar 1.0.0 | tar -x -C "C:/Program Files/My Addon"',
            id="path_with_spaces"
        ),
        pytest.param(
            "C:\\Users\\test\\addon",
            "dev",
            'stash=`git stash create`; git archive --format tar $stash | tar -x -C "C:/Users/test/addon"',
            id="dev_version"
        ),
    ]
)
def test_archive_path_handling(git, path, version, expected_cmd):
    with patch('aab.git.call_shell') as mock_call_shell:
        mock_call_shell.return_value = True
        result = git.archive(version, Path(path))
        mock_call_shell.assert_called_once_with(expected_cmd)
        assert result is True


@pytest.mark.parametrize(
    "version, shell_outputs, expected", [
        pytest.param(
            "1.0.0",
            [],  # No shell commands needed for exact version
            "1.0.0",
            id="exact_version"
        ),
        pytest.param(
            None,
            ["2.0.0"],  # Just needs describe
            "2.0.0",
            id="default_version"
        ),
        pytest.param(
            "release",
            ["3.0.0"],  # Just needs describe
            "3.0.0",
            id="release_version"
        ),
        pytest.param(
            None,
            [False, "abc123"],  # Needs describe + fallback
            "abc123",
            id="no_tags_fallback"
        ),
    ]
)
def test_parse_version(git, version, shell_outputs, expected):
    with patch('aab.git.call_shell') as mock_call_shell:
        mock_call_shell.side_effect = shell_outputs
        result = git.parse_version(version)
        assert result == expected
        assert mock_call_shell.call_count == len(shell_outputs)


@pytest.mark.parametrize(
    "version, shell_output, expected", [
        pytest.param(
            "1.0.0",
            "1234567890",
            1234567890,
            id="tag_version"
        ),
        pytest.param(
            "dev",
            "1000\n2000\n3000",
            3000,
            id="uncommitted_changes"
        ),
    ]
)
def test_modtime(git, version, shell_output, expected):
    with patch('aab.git.call_shell') as mock_call_shell:
        mock_call_shell.return_value = shell_output
        result = git.modtime(version)
        assert result == expected


def test_archive_invalid_inputs(git):
    assert git.archive(None, Path("/some/path")) is False
    assert git.archive("1.0.0", None) is False