from unittest import TestCase
from unittest.mock import patch, Mock
from subprocess import TimeoutExpired

from cyclarity_in_vehicle_sdk.utils.linux.linux_utils import (
    CommandResult,
    _run_command_with_output,
    install_linux_package,
    run_bash_command
)


class TestCommandResult(TestCase):
    """Test the CommandResult named tuple."""

    def test_command_result_creation(self):
        """Test creating a CommandResult instance."""
        result = CommandResult(success=True, stdout="test output", stderr="")
        self.assertTrue(result.success)
        self.assertEqual(result.stdout, "test output")
        self.assertEqual(result.stderr, "")

    def test_command_result_immutability(self):
        """Test that CommandResult is immutable."""
        result = CommandResult(success=True, stdout="test", stderr="")
        with self.assertRaises(AttributeError):
            result.success = False


class TestRunCommandWithOutput(TestCase):
    """Test the internal _run_command_with_output function."""

    @patch('cyclarity_in_vehicle_sdk.utils.linux.linux_utils.subprocess.run')
    def test_successful_command(self, mock_run):
        """Test successful command execution."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "command output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = _run_command_with_output("echo 'test'")

        self.assertTrue(result.success)
        self.assertEqual(result.stdout, "command output")
        self.assertEqual(result.stderr, "")
        mock_run.assert_called_once()

    @patch('cyclarity_in_vehicle_sdk.utils.linux.linux_utils.subprocess.run')
    def test_failed_command(self, mock_run):
        """Test failed command execution."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "command failed"
        mock_run.return_value = mock_result

        result = _run_command_with_output("invalid_command")

        self.assertFalse(result.success)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "command failed")

    @patch('cyclarity_in_vehicle_sdk.utils.linux.linux_utils.subprocess.run')
    def test_timeout_exception(self, mock_run):
        """Test command timeout handling."""
        mock_run.side_effect = TimeoutExpired("test_command", 30)

        result = _run_command_with_output("sleep 60", timeout=30)

        self.assertFalse(result.success)
        self.assertEqual(result.stdout, "")
        self.assertIn("Command timed out after 30 seconds", result.stderr)

    @patch('cyclarity_in_vehicle_sdk.utils.linux.linux_utils.subprocess.run')
    def test_general_exception(self, mock_run):
        """Test general exception handling."""
        mock_run.side_effect = Exception("Unexpected error")

        result = _run_command_with_output("test_command")

        self.assertFalse(result.success)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "Unexpected error")

    @patch('cyclarity_in_vehicle_sdk.utils.linux.linux_utils.subprocess.run')
    def test_command_parameters(self, mock_run):
        """Test that subprocess.run is called with correct parameters."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        _run_command_with_output("test_command", timeout=60)

        mock_run.assert_called_once_with(
            "test_command",
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            check=False
        )


class TestInstallLinuxPackage(TestCase):
    """Test the install_linux_package function."""

    @patch('cyclarity_in_vehicle_sdk.utils.linux.linux_utils._run_command_with_output')
    def test_successful_package_installation(self, mock_run_command):
        """Test successful package installation."""
        mock_run_command.return_value = CommandResult(
            success=True,
            stdout="Package installed successfully",
            stderr=""
        )

        result = install_linux_package("curl")

        self.assertTrue(result.success)
        self.assertEqual(result.stdout, "Package installed successfully")
        self.assertEqual(result.stderr, "")
        mock_run_command.assert_called_once_with(
            "apt-get install -y curl",
            timeout=600
        )

    @patch('cyclarity_in_vehicle_sdk.utils.linux.linux_utils._run_command_with_output')
    def test_failed_package_installation(self, mock_run_command):
        """Test failed package installation."""
        mock_run_command.return_value = CommandResult(
            success=False,
            stdout="",
            stderr="Package not found"
        )

        result = install_linux_package("nonexistent_package")

        self.assertFalse(result.success)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "Package not found")

    def test_empty_package_name(self):
        """Test installation with empty package name."""
        result = install_linux_package("")
        self.assertFalse(result.success)
        self.assertEqual(result.stderr, "Package name cannot be empty")

    def test_whitespace_package_name(self):
        """Test installation with whitespace-only package name."""
        result = install_linux_package("   ")
        self.assertFalse(result.success)
        self.assertEqual(result.stderr, "Package name cannot be empty")

    def test_package_name_stripping(self):
        """Test that package name is properly stripped."""
        with patch('cyclarity_in_vehicle_sdk.utils.linux.linux_utils._run_command_with_output') as mock_run_command:
            mock_run_command.return_value = CommandResult(
                success=True,
                stdout="Package installed",
                stderr=""
            )

            result = install_linux_package("  curl  ")

            self.assertTrue(result.success)
            mock_run_command.assert_called_once_with(
                "apt-get install -y curl",
                timeout=600
            )

    @patch('cyclarity_in_vehicle_sdk.utils.linux.linux_utils._run_command_with_output')
    def test_package_installation_timeout(self, mock_run_command):
        """Test package installation timeout."""
        mock_run_command.return_value = CommandResult(
            success=False,
            stdout="",
            stderr="Command timed out after 600 seconds"
        )

        result = install_linux_package("large_package")

        self.assertFalse(result.success)
        self.assertIn("Command timed out", result.stderr)


class TestRunBashCommand(TestCase):
    """Test the run_bash_command function."""

    @patch('cyclarity_in_vehicle_sdk.utils.linux.linux_utils._run_command_with_output')
    def test_successful_command(self, mock_run_command):
        """Test successful bash command execution."""
        mock_run_command.return_value = CommandResult(
            success=True,
            stdout="command output",
            stderr=""
        )

        result = run_bash_command("ls -la")

        self.assertTrue(result.success)
        self.assertEqual(result.stdout, "command output")
        self.assertEqual(result.stderr, "")
        mock_run_command.assert_called_once_with("ls -la", timeout=300)

    @patch('cyclarity_in_vehicle_sdk.utils.linux.linux_utils._run_command_with_output')
    def test_failed_command(self, mock_run_command):
        """Test failed bash command execution."""
        mock_run_command.return_value = CommandResult(
            success=False,
            stdout="",
            stderr="command not found"
        )

        result = run_bash_command("nonexistent_command")

        self.assertFalse(result.success)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "command not found")

    def test_empty_command(self):
        """Test execution with empty command."""
        result = run_bash_command("")
        self.assertFalse(result.success)
        self.assertEqual(result.stderr, "Command cannot be empty")

    def test_whitespace_command(self):
        """Test execution with whitespace-only command."""
        result = run_bash_command("   ")
        self.assertFalse(result.success)
        self.assertEqual(result.stderr, "Command cannot be empty")

    def test_command_stripping(self):
        """Test that command is properly stripped."""
        with patch('cyclarity_in_vehicle_sdk.utils.linux.linux_utils._run_command_with_output') as mock_run_command:
            mock_run_command.return_value = CommandResult(
                success=True,
                stdout="output",
                stderr=""
            )

            result = run_bash_command("  ls -la  ")

            self.assertTrue(result.success)
            mock_run_command.assert_called_once_with("ls -la", timeout=300)

    @patch('cyclarity_in_vehicle_sdk.utils.linux.linux_utils._run_command_with_output')
    def test_custom_timeout(self, mock_run_command):
        """Test command execution with custom timeout."""
        mock_run_command.return_value = CommandResult(
            success=True,
            stdout="output",
            stderr=""
        )

        result = run_bash_command("long_running_command", timeout=60)

        self.assertTrue(result.success)
        mock_run_command.assert_called_once_with("long_running_command", timeout=60)

    @patch('cyclarity_in_vehicle_sdk.utils.linux.linux_utils._run_command_with_output')
    def test_command_with_output_and_error(self, mock_run_command):
        """Test command that produces both output and error."""
        mock_run_command.return_value = CommandResult(
            success=True,
            stdout="some output",
            stderr="some warning"
        )

        result = run_bash_command("command_with_warnings")

        self.assertTrue(result.success)
        self.assertEqual(result.stdout, "some output")
        self.assertEqual(result.stderr, "some warning")


class TestIntegrationScenarios(TestCase):
    """Test integration scenarios and edge cases."""

    @patch('cyclarity_in_vehicle_sdk.utils.linux.linux_utils._run_command_with_output')
    def test_multiple_package_installations(self, mock_run_command):
        """Test installing multiple packages."""
        packages = ["curl", "wget", "git"]
        
        for package in packages:
            mock_run_command.return_value = CommandResult(
                success=True,
                stdout=f"{package} installed",
                stderr=""
            )
            
            result = install_linux_package(package)
            self.assertTrue(result.success)
            self.assertIn(package, result.stdout)

    @patch('cyclarity_in_vehicle_sdk.utils.linux.linux_utils._run_command_with_output')
    def test_system_commands(self, mock_run_command):
        """Test various system commands."""
        test_commands = [
            ("uname -a", "Linux test-host 5.4.0"),
            ("whoami", "testuser"),
            ("pwd", "/home/testuser"),
        ]
        
        for command, expected_output in test_commands:
            mock_run_command.return_value = CommandResult(
                success=True,
                stdout=expected_output,
                stderr=""
            )
            
            result = run_bash_command(command)
            self.assertTrue(result.success)
            self.assertIn(expected_output, result.stdout)
