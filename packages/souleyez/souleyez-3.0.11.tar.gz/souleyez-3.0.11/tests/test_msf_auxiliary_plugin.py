"""Tests for msf_auxiliary plugin command building.

These tests verify that the Metasploit auxiliary plugin correctly builds
commands for different module types, particularly handling SMB1 compatibility.
"""

import pytest


class TestMsfAuxiliarySmbSupport:
    """Test SMB1 compatibility for older systems like Metasploitable2."""

    def test_smb_enumshares_sets_smbdirect_false(self):
        """smb_enumshares should set SMBDirect false for SMB1 compatibility.

        SMB1-only servers (like Metasploitable2) fail with modern
        Metasploit SMB modules unless SMBDirect is set to false.

        Error without fix: "Invalid packet received when trying to
        enumerate shares - The response seems to be an SMB1
        NtCreateAndxResponse but an error occurs while parsing it."

        Regression test for job #749 failure.
        """
        from souleyez.plugins.msf_auxiliary import MsfAuxiliaryPlugin

        plugin = MsfAuxiliaryPlugin()
        result = plugin.build_command(
            target="192.168.1.240",
            args=["auxiliary/scanner/smb/smb_enumshares"],
        )

        if result is None:
            pytest.fail("build_command returned None")

        cmd_list = result.get("cmd", [])
        command_str = " ".join(cmd_list)

        # Should have SMBDirect false for legacy SMB1 support
        assert (
            "SMBDirect" in command_str and "false" in command_str.lower()
        ), f"Missing SMBDirect false. Command: {command_str}"

    def test_smb_enumusers_sets_smbdirect_false(self):
        """smb_enumusers should also set SMBDirect false."""
        from souleyez.plugins.msf_auxiliary import MsfAuxiliaryPlugin

        plugin = MsfAuxiliaryPlugin()
        result = plugin.build_command(
            target="192.168.1.240",
            args=["auxiliary/scanner/smb/smb_enumusers"],
        )

        if result is None:
            pytest.fail("build_command returned None")

        cmd_list = result.get("cmd", [])
        command_str = " ".join(cmd_list)

        assert (
            "SMBDirect" in command_str and "false" in command_str.lower()
        ), f"Missing SMBDirect false. Command: {command_str}"

    def test_smb_version_sets_smbdirect_false(self):
        """smb_version should also set SMBDirect false."""
        from souleyez.plugins.msf_auxiliary import MsfAuxiliaryPlugin

        plugin = MsfAuxiliaryPlugin()
        result = plugin.build_command(
            target="192.168.1.240",
            args=["auxiliary/scanner/smb/smb_version"],
        )

        if result is None:
            pytest.fail("build_command returned None")

        cmd_list = result.get("cmd", [])
        command_str = " ".join(cmd_list)

        assert (
            "SMBDirect" in command_str and "false" in command_str.lower()
        ), f"Missing SMBDirect false. Command: {command_str}"

    def test_non_smb_module_no_smbdirect(self):
        """Non-SMB modules should not have SMBDirect option."""
        from souleyez.plugins.msf_auxiliary import MsfAuxiliaryPlugin

        plugin = MsfAuxiliaryPlugin()
        result = plugin.build_command(
            target="192.168.1.240",
            args=["auxiliary/scanner/ftp/ftp_version"],
        )

        if result is None:
            pytest.fail("build_command returned None")

        cmd_list = result.get("cmd", [])
        command_str = " ".join(cmd_list)

        # Non-SMB modules should NOT have SMBDirect
        assert (
            "SMBDirect" not in command_str
        ), f"FTP should not have SMBDirect. Command: {command_str}"

    def test_user_provided_smbdirect_preserved(self):
        """User-specified SMBDirect value should be preserved."""
        from souleyez.plugins.msf_auxiliary import MsfAuxiliaryPlugin

        plugin = MsfAuxiliaryPlugin()
        result = plugin.build_command(
            target="192.168.1.240",
            args=["auxiliary/scanner/smb/smb_enumshares", "SMBDirect=true"],
        )

        if result is None:
            pytest.fail("build_command returned None")

        cmd_list = result.get("cmd", [])
        command_str = " ".join(cmd_list)

        # User explicitly set SMBDirect=true, should be preserved
        # The command should have only ONE SMBDirect setting (the user's)
        assert (
            command_str.count("SMBDirect") == 1
        ), f"Should have exactly one SMBDirect. Command: {command_str}"
        assert (
            "SMBDirect true" in command_str or "SMBDirect=true" in command_str
        ), f"User SMBDirect=true should be preserved. Command: {command_str}"
