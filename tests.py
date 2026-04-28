import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from main import VaultDirError, decrypt_vault, encrypt_directory, main


class VaultDirTests(unittest.TestCase):
    def test_version_flag_prints_project_version(self) -> None:
        stdout = io.StringIO()
        with (
            patch("sys.argv", ["vaultdir", "--version"]),
            patch("sys.stdout", stdout),
        ):
            with self.assertRaises(SystemExit) as exc:
                main()

        self.assertEqual(exc.exception.code, 0)
        self.assertEqual(stdout.getvalue().strip(), "vaultdir 0.0.2")

    def test_encrypt_decrypt_round_trip_uses_archived_name_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            source = base / "input"
            source.mkdir()
            (source / "id_rsa").write_text("secret\n", encoding="utf-8")
            nested = source / "subdir"
            nested.mkdir()
            (nested / "config").write_text("nested\n", encoding="utf-8")

            vault_path = base / "input.vault"

            with patch("main.getpass.getpass", side_effect=["testpass123", "testpass123"]):
                encrypt_directory(source, vault_path, force=False)

            source.rename(base / "input.original")

            with patch("main.getpass.getpass", return_value="testpass123"):
                output_dir = decrypt_vault(vault_path, None, force=False)

            self.assertEqual(output_dir, base / "input")
            self.assertEqual((output_dir / "id_rsa").read_text(encoding="utf-8"), "secret\n")
            self.assertEqual(
                (output_dir / "subdir" / "config").read_text(encoding="utf-8"),
                "nested\n",
            )

    def test_decrypt_output_path_is_exact_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            source = base / "input"
            source.mkdir()
            (source / "id_rsa").write_text("secret\n", encoding="utf-8")

            vault_path = base / "input.vault"
            output_dir = base / "restored"

            with patch("main.getpass.getpass", side_effect=["testpass123", "testpass123"]):
                encrypt_directory(source, vault_path, force=False)

            with patch("main.getpass.getpass", return_value="testpass123"):
                restored = decrypt_vault(vault_path, output_dir, force=False)

            self.assertEqual(restored, output_dir)
            self.assertEqual((output_dir / "id_rsa").read_text(encoding="utf-8"), "secret\n")

    def test_wrong_password_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            source = base / "input"
            source.mkdir()
            (source / "file.txt").write_text("secret\n", encoding="utf-8")

            vault_path = base / "input.vault"
            output_dir = base / "restored"

            with patch("main.getpass.getpass", side_effect=["testpass123", "testpass123"]):
                encrypt_directory(source, vault_path, force=False)

            with patch("main.getpass.getpass", return_value="wrongpass"):
                with self.assertRaises(VaultDirError):
                    decrypt_vault(vault_path, output_dir, force=False)


if __name__ == "__main__":
    unittest.main()
