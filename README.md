# vaultdir

`vaultdir` encrypts a directory into a single password-protected `.vault` file and can decrypt it again later.

## Install

```bash
uv tool install git+https://github.com/diversen/vaultdir.git
```

## Usage

Encrypt a directory:

```bash
vaultdir encrypt some-dir
```

This creates `some-dir.vault`.

Decrypt a vault:

```bash
vaultdir decrypt some-dir.vault
```

This restores the archived directory in the current directory. For example,
`some-dir.vault` created from `some-dir` restores to `./some-dir`.

## Options

```bash
vaultdir --version
vaultdir encrypt some-dir -o backup.vault
vaultdir decrypt backup.vault -o restored-dir
vaultdir decrypt backup.vault -o restored-dir --force
```

When `-o restored-dir` is used with `decrypt`, the archive is restored directly into
`restored-dir`.

## Notes

- The password is prompted interactively and is not passed on the command line.
- Existing output files or directories are not overwritten unless `--force` is used.
- The archive is encrypted with `scrypt` for key derivation and `AES-256-GCM` for authenticated encryption.
- Security details: [docs.md](./docs.md)
- Legal note: [legal.md](./legal.md)
