# vaultdir security notes

`vaultdir` encrypts a directory into a single `.vault` file using password-based encryption.

## What is encrypted

The input directory is archived as a tar stream and encrypted into one output file.

The tar plaintext is not written as a separate temporary tar file during encryption.

During decryption, plaintext files are extracted into a temporary directory next to the final output directory. After authentication succeeds, that temporary directory is renamed into place. If decryption fails, the temporary directory is deleted.

## Cryptography used

- Key derivation: `scrypt`
- Encryption: `AES-256-GCM`
- Salt size: 16 bytes
- Nonce size: 12 bytes
- Authentication tag: 16 bytes
- Derived key size: 32 bytes

Current `scrypt` parameters:

- `N = 2^15`
- `r = 8`
- `p = 1`

These parameters make each password guess consume meaningful CPU and memory, which raises the cost of offline password guessing.

## File format

Each `.vault` file contains:

1. Magic bytes: `VAULTDIR\0`
2. Format version
3. `scrypt` parameters: `N`, `r`, `p`
4. Random salt
5. Random nonce
6. Ciphertext
7. GCM authentication tag

The salt and nonce are not secrets. They are stored in the file because they are needed for decryption.

## Why this is secure

This program relies on two standard security properties:

1. `scrypt` turns a password into an encryption key while making each password guess expensive.
2. `AES-256-GCM` provides both confidentiality and integrity.

That means:

- Without the password, an attacker should not be able to recover the directory contents.
- If the `.vault` file is modified, decryption should fail.
- A wrong password and a corrupted file both fail authentication.

`scrypt` is memory-hard. This is important because an attacker who steals a `.vault` file can try passwords offline. Memory-hard key derivation makes each guess cost more RAM and computation, which reduces the attacker's efficiency, especially on highly parallel hardware.

`AES-256-GCM` is a well-established authenticated-encryption mode. It protects the secrecy of the tar stream and verifies that the ciphertext has not been altered.

## What this does not protect against

This tool is not magic. Security still depends on the environment and the password.

It does not protect against:

- A weak or reused password
- Malware or a keylogger on the machine
- A compromised machine during encryption or decryption
- Someone who already knows the password
- Plaintext leakage from backups, swap, filesystem snapshots, or other system-level storage

If the password is strong and random, offline brute force becomes impractical. If the password is weak, the attacker can still guess it eventually.

## Important implementation details

### Nonce handling

`AES-GCM` requires that a nonce is never reused with the same key. `vaultdir` generates a fresh random 12-byte nonce for every encryption.

### Output safety

- Existing output paths are not overwritten unless `--force` is used.
- Archive extraction rejects absolute paths.
- Archive extraction rejects `..` path traversal.
- Archive extraction rejects symbolic links and hard links.
- Decryption publishes output only after GCM authentication succeeds.

## Practical security guidance

- Use a long, unique password or passphrase.
- A truly random 64-character password is far stronger than this tool is likely to need in practice.
- Keep the machine itself secure.
- Be careful where you decrypt, since plaintext files will exist on disk after decryption.

## Security summary

The design is secure because it combines:

- a standard password-based KDF designed to slow offline guessing
- a standard authenticated-encryption mode
- random salt and nonce generation for every archive
- extraction checks to prevent obvious archive abuse

In practice, the most likely failure is not a break in `AES-256-GCM`. It is usually one of:

- weak password choice
- endpoint compromise
- operational leakage of plaintext after decryption

## Potential improvements

The biggest practical improvement would be better tuning of the `scrypt` cost parameters:

- `N`
- `r`
- `p`

These values are already stored in the vault file, so the format supports future tuning without breaking decryption of old vaults.

Why this matters:

- Higher `scrypt` cost makes offline password guessing more expensive.
- It raises CPU and memory cost for attackers.
- It also raises CPU and memory cost for the legitimate user during encryption and decryption.

So this is mainly a tradeoff between usability and offline attack resistance.

Possible future improvements:

- Add named security profiles such as `standard`, `hard`, and `max`
- Raise the default `scrypt` cost if testing shows it is still practical on normal machines
- Add a benchmark command to help choose a suitable `scrypt` profile
- Document the current `scrypt` cost in terms of approximate RAM usage per password guess
- Add an optional mode for even stricter handling of decrypted output and temporary plaintext
