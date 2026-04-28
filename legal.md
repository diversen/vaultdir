# Legal note

`vaultdir` is encryption software.

In many countries, using encryption software for personal file protection is legal. However, encryption laws are not the same everywhere.

Possible legal issues can include:

- export controls
- import restrictions
- sanctions compliance
- registration or certification rules in some jurisdictions

So `vaultdir` should not be described as guaranteed legal everywhere in the world.

For most users, the main legal question is usually not whether password-based file encryption exists, but whether distributing or exporting the software into a specific jurisdiction is allowed.

This project does not provide legal advice. If you plan to distribute, export, or use this software in a regulated environment or jurisdiction, check the applicable laws and rules first.

## Region notes

As of April 28, 2026, the following is a practical summary for the United States, the European Union, and China.

### United States

In the United States, encryption software is regulated under the Export Administration Regulations (`EAR`), especially Category 5, Part 2.

For a project like `vaultdir`, the main issue is usually export and distribution compliance, not ordinary local personal use.

Important points:

- Many encryption products can be exported under License Exception `ENC`, depending on classification, destination, end user, and reporting requirements.
- Publicly available encryption source code can fall outside the `EAR` after the required notification steps are completed.
- Some destinations and use cases remain restricted.

Practical takeaway:

- Personal local use is not the obvious legal problem.
- Publishing and exporting the software may require compliance with BIS rules.

### European Union

In the European Union, encryption software can fall under the dual-use export control regime in Regulation `(EU) 2021/821`, including Category 5, Part 2 and entries such as `5D002`.

For a project like `vaultdir`, the main issue is export control, not normal private use inside the EU.

Important points:

- Annex I includes information-security and encryption-related software.
- The regulation includes the cryptography note and related carve-outs for some mass-market items.
- Category 5, Part 2 also states that products accompanying their user for the user's personal use are not controlled there.

Practical takeaway:

- Personal use is not the main concern.
- Cross-border export and commercial distribution are the main legal questions.
- Enforcement and penalties are handled by member states, so practice can vary between countries.

### China

China's Cryptography Law expressly allows citizens, legal persons, and other organizations to use commercial cryptography to protect cyber and information security in accordance with law.

At the same time, China regulates import, export, certification, and some national-security-related uses of commercial cryptography.

Important points:

- Commercial cryptography use is allowed in principle.
- Import licensing and export control can apply where national security or public interests are involved.
- The law states that import licensing and export control do not apply to commercial cryptography used in mass-consumption products.
- Operators of critical information infrastructure can be subject to additional review and compliance requirements.

Practical takeaway:

- Normal personal use does not appear to be broadly prohibited.
- Import, export, and regulated commercial or infrastructure-related contexts are the main legal concern.

See also:

- [docs.md](./docs.md)

## Sources

- U.S. BIS encryption controls overview: https://www.bis.gov/learn-support/encryption-controls?id=1160
- U.S. `EAR § 740.17`: https://www.bis.gov/regulations/ear/740
- U.S. publicly available encryption source code guidance: https://www.bis.gov/learn-support/encryption-controls/encryption-items-not-subject-to-ear
- U.S. `EAR § 742.15`: https://www.bis.gov/regulations/ear/742
- EU dual-use summary: https://eur-lex.europa.eu/EN/legal-content/summary/dual-use-export-controls.html
- EU Regulation `(EU) 2021/821`: https://eur-lex.europa.eu/eli/reg/2021/821/2023-12-16/eng
- EU Annex I / Category 5, Part 2: https://eur-lex.europa.eu/legal-content/EN-ES/TXT/?uri=CELEX%3A32021R0821
- China Cryptography Law: https://www.npc.gov.cn/englishnpc/c2759/c23934/202009/t20200929_384279.html
- China 2023 revised commercial cryptography regulations summary: https://en.moj.gov.cn/2023-05/25/c_889504.htm
