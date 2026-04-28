import argparse
import getpass
import importlib.metadata
import os
import shutil
import struct
import sys
import tarfile
import tempfile
import tomllib
from pathlib import Path, PurePosixPath

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


MAGIC = b"VAULTDIR\x00"
VERSION = 1
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
TAG_SIZE = 16
SCRYPT_N = 2**15
SCRYPT_R = 8
SCRYPT_P = 1
HEADER_STRUCT = struct.Struct(">9sBIII")
PROJECT_ROOT = Path(__file__).resolve().parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"


class VaultDirError(Exception):
    pass


class EncryptingWriter:
    def __init__(self, raw_file, encryptor) -> None:
        self.raw_file = raw_file
        self.encryptor = encryptor

    def write(self, data: bytes) -> int:
        if not data:
            return 0
        self.raw_file.write(self.encryptor.update(data))
        return len(data)

    def flush(self) -> None:
        self.raw_file.flush()


class DecryptingReader:
    def __init__(self, raw_file, decryptor, ciphertext_length: int) -> None:
        self.raw_file = raw_file
        self.decryptor = decryptor
        self.remaining = ciphertext_length

    def read(self, size: int = -1) -> bytes:
        if self.remaining <= 0:
            return b""
        if size is None or size < 0 or size > self.remaining:
            size = self.remaining
        chunk = self.raw_file.read(size)
        if not chunk:
            raise VaultDirError("vault file is truncated")
        self.remaining -= len(chunk)
        return self.decryptor.update(chunk)

    def readable(self) -> bool:
        return True


def derive_key(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    kdf = Scrypt(salt=salt, length=KEY_SIZE, n=n, r=r, p=p)
    return kdf.derive(password.encode("utf-8"))


def prompt_password(confirm: bool) -> str:
    password = getpass.getpass("Password: ")
    if not password:
        raise VaultDirError("password cannot be empty")
    if confirm:
        repeated = getpass.getpass("Confirm password: ")
        if password != repeated:
            raise VaultDirError("passwords did not match")
    return password


def default_encrypt_output(directory: Path) -> Path:
    return directory.parent / f"{directory.name}.vault"


def get_program_version() -> str:
    try:
        return importlib.metadata.version("vaultdir")
    except importlib.metadata.PackageNotFoundError:
        pass

    with PYPROJECT_PATH.open("rb") as handle:
        pyproject = tomllib.load(handle)
    return pyproject["project"]["version"]


def ensure_output_path(path: Path, force: bool) -> None:
    if not path.exists():
        return
    if not force:
        raise VaultDirError(f"output already exists: {path}")
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def validate_tar_member(member: tarfile.TarInfo, output_dir: Path) -> None:
    member_path = PurePosixPath(member.name)
    if member_path.is_absolute():
        raise VaultDirError(f"archive contains absolute path: {member.name}")
    if ".." in member_path.parts:
        raise VaultDirError(f"archive contains parent traversal: {member.name}")
    if member.issym() or member.islnk():
        raise VaultDirError(f"archive contains unsupported link: {member.name}")
    target = (output_dir / Path(*member_path.parts)).resolve()
    base = output_dir.resolve()
    if os.path.commonpath([str(base), str(target)]) != str(base):
        raise VaultDirError(f"archive escapes output directory: {member.name}")


def extract_streaming_tar(archive: tarfile.TarFile, output_dir: Path) -> str:
    root_name = None
    directory_modes: list[tuple[Path, int]] = []
    for member in archive:
        validate_tar_member(member, output_dir)
        member_root = PurePosixPath(member.name).parts[0]
        if root_name is None:
            root_name = member_root
        elif member_root != root_name:
            raise VaultDirError("archive must contain exactly one top-level directory")

        destination = output_dir / Path(*PurePosixPath(member.name).parts)
        if member.isdir():
            destination.mkdir(parents=True, exist_ok=True)
            directory_modes.append((destination, member.mode))
            continue
        if not member.isfile():
            raise VaultDirError(f"archive contains unsupported member: {member.name}")

        destination.parent.mkdir(parents=True, exist_ok=True)
        extracted = archive.extractfile(member)
        if extracted is None:
            raise VaultDirError(f"failed to read archived file: {member.name}")
        with extracted, destination.open("wb") as handle:
            shutil.copyfileobj(extracted, handle)
        os.chmod(destination, member.mode)

    if root_name is None:
        raise VaultDirError("archive is empty")
    for directory, mode in reversed(directory_modes):
        os.chmod(directory, mode)
    return root_name


def encrypt_directory(source_dir: Path, output_file: Path, force: bool) -> None:
    if not source_dir.is_dir():
        raise VaultDirError(f"not a directory: {source_dir}")
    ensure_output_path(output_file, force)
    password = prompt_password(confirm=True)
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt, SCRYPT_N, SCRYPT_R, SCRYPT_P)
    with output_file.open("wb") as raw_file:
        header = HEADER_STRUCT.pack(MAGIC, VERSION, SCRYPT_N, SCRYPT_R, SCRYPT_P)
        raw_file.write(header)
        raw_file.write(salt)
        raw_file.write(nonce)
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
        encryptor = cipher.encryptor()
        writer = EncryptingWriter(raw_file, encryptor)
        with tarfile.open(fileobj=writer, mode="w|") as archive:
            archive.add(source_dir, arcname=source_dir.name, recursive=True)
        raw_file.write(encryptor.finalize())
        raw_file.write(encryptor.tag)


def decrypt_vault(vault_file: Path, output_dir: Path | None, force: bool) -> Path:
    if not vault_file.is_file():
        raise VaultDirError(f"not a file: {vault_file}")
    minimum_size = HEADER_STRUCT.size + SALT_SIZE + NONCE_SIZE + TAG_SIZE
    file_size = vault_file.stat().st_size
    if file_size < minimum_size:
        raise VaultDirError("vault file is too small")
    password = prompt_password(confirm=False)
    temp_parent = output_dir.parent if output_dir else vault_file.parent
    temp_output = Path(
        tempfile.mkdtemp(prefix=f".{vault_file.stem}.tmp.", dir=str(temp_parent))
    )
    try:
        with vault_file.open("rb") as raw_file:
            header = raw_file.read(HEADER_STRUCT.size)
            magic, version, n, r, p = HEADER_STRUCT.unpack(header)
            if magic != MAGIC:
                raise VaultDirError("file is not a vaultdir archive")
            if version != VERSION:
                raise VaultDirError(f"unsupported vault version: {version}")

            salt = raw_file.read(SALT_SIZE)
            nonce = raw_file.read(NONCE_SIZE)
            if len(salt) != SALT_SIZE or len(nonce) != NONCE_SIZE:
                raise VaultDirError("vault file is truncated")

            key = derive_key(password, salt, n, r, p)
            ciphertext_length = file_size - HEADER_STRUCT.size - SALT_SIZE - NONCE_SIZE - TAG_SIZE
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
            decryptor = cipher.decryptor()
            reader = DecryptingReader(raw_file, decryptor, ciphertext_length)

            with tarfile.open(fileobj=reader, mode="r|") as archive:
                root_name = extract_streaming_tar(archive, temp_output)

            tag = raw_file.read(TAG_SIZE)
            if len(tag) != TAG_SIZE:
                raise VaultDirError("vault file is truncated")
            decryptor.finalize_with_tag(tag)

        extracted_root = temp_output / root_name
        final_output = output_dir if output_dir else vault_file.parent / root_name
        ensure_output_path(final_output, force)
        extracted_root.replace(final_output)
        shutil.rmtree(temp_output)
        return final_output
    except InvalidTag as exc:
        if temp_output.exists():
            shutil.rmtree(temp_output)
        raise VaultDirError("wrong password or corrupted file") from exc
    except tarfile.TarError as exc:
        if temp_output.exists():
            shutil.rmtree(temp_output)
        raise VaultDirError("wrong password or corrupted file") from exc
    except Exception:
        if temp_output.exists():
            shutil.rmtree(temp_output)
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vaultdir",
        description="Encrypt or decrypt a directory into a password-protected vault file.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_program_version()}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    encrypt_parser = subparsers.add_parser("encrypt", help="encrypt a directory")
    encrypt_parser.add_argument("source", type=Path, help="directory to encrypt")
    encrypt_parser.add_argument("-o", "--output", type=Path, help="output vault file")
    encrypt_parser.add_argument(
        "-f", "--force", action="store_true", help="overwrite an existing output file"
    )

    decrypt_parser = subparsers.add_parser("decrypt", help="decrypt a vault file")
    decrypt_parser.add_argument("source", type=Path, help="vault file to decrypt")
    decrypt_parser.add_argument("-o", "--output", type=Path, help="output directory")
    decrypt_parser.add_argument(
        "-f", "--force", action="store_true", help="overwrite an existing output path"
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "encrypt":
            output = args.output if args.output else default_encrypt_output(args.source)
            encrypt_directory(args.source, output, args.force)
            print(f"Created {output}")
        else:
            output = decrypt_vault(args.source, args.output, args.force)
            print(f"Extracted to {output}")
    except VaultDirError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
