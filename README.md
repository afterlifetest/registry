# Afterlife Test registry – independent copy

This repository keeps a daily copy of the public registry of [Afterlife Test](https://afterlifetest.com). The same copy is stored at the Internet Archive: <https://archive.org/details/afterlifetest-registry>.

**Why it exists.** A seal may need to wait fifty years or more. A test lasts only as long as the place that keeps it, and websites close. This copy lets anyone check a phrase against any seal even if afterlifetest.com no longer exists.

**If you know the phrase, you can check it here. It costs nothing.**

## Check a phrase

- **In a browser:** open `verify.html` (from GitHub Pages, from the Internet Archive item, or as a file next to `registry.json` on your computer). Type the seal number and the phrase. Everything is computed on your device and nothing is sent anywhere.
- **On the command line** (Python 3, nothing to install):

  ```
  python3 check.py phrase registry.json <seal number> "the phrase you received"
  ```

A match found here is not recorded anywhere. If the website still exists, enter the phrase on the seal's page as well, so the opening is logged publicly with its date.

## Check that nobody altered the registry

```
python3 check.py chain registry.json                       # recompute both hash chains
python3 check.py append snapshots/2026-11.json registry.json # nothing old changed or removed
```

Every seal contains the fingerprint of the one before it, and so does every change log entry. The daily copy is refused if any old entry was altered or removed, so a change made on the website after the fact would show up here as a failed run.

## What is in the copy

| Kept | Not kept |
| --- | --- |
| Seal number, date, salt, phrase fingerprint, number of rounds | Names and nicknames |
| Both hash chains | The source field of death reports (outside the change log) |
| Counters and statuses: attempts, opened, sign of life, date of death | The text of opening accounts (only its fingerprint) |
| The change log, including any source link given in a death report (it is part of the chain) | |

Names stay on the live site, where their creators can hide them. The fingerprint of each name stays in the chain, so the chain still checks out.

## Files

| File | What it is |
| --- | --- |
| `registry.json` | The latest copy |
| `snapshots/YYYY-MM.json` | The first copy of each month, kept for ever |
| `SHA256SUMS` | Checksums of all copies |
| `verify.html` | Offline phrase checker for the browser |
| `check.py` | Command-line checker |
| `.github/workflows/mirror.yml` | The daily job that makes the copy |

## Make your own copy

Fork this repository and enable Actions in the fork (GitHub pauses scheduled jobs in forks until you do). Your fork will then keep its own daily copy. The more independent copies exist, the harder the registry is to lose.

## Setup notes for the maintainer

1. Create a public repository, for example `afterlifetest/registry`, with the files of this folder.
2. *Settings → Actions → General → Workflow permissions:* allow read and write.
3. *Settings → Pages:* deploy from the `main` branch, so `verify.html` opens at `https://<user>.github.io/registry/verify.html`.
4. Internet Archive: create a free account, get the S3 keys at <https://archive.org/account/s3.php>, and add them as repository secrets `IA_ACCESS` and `IA_SECRET`. Without them the copy is kept on GitHub only.
5. Run the workflow once by hand (*Actions → Mirror the registry → Run workflow*).
