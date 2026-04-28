# encrypt-dir

This should be a simple tool written in Python that takes a single directory and encrypts it. The encryption should be password-based so there is no need to share keys.

Use case: I have made some new `ssh` keys on my work computer and I need to share them with my work laptop that is at home in a secure way.

The command should be named `vaultdir`.

Usage should be something like:

    vaultdir --encrypt some-dir

This encrypts the complete directory and all files into a single file, for example `some-dir.vault`.

    vaultdir --decrypt some-dir.vault

I enter the password and now have the decrypted original `some-dir`.
