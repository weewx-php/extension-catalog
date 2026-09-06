# weewx-php extension catalog

`catalog.json` is the approval list used by **Admin → Extensions** in
[weewx-php](https://github.com/weewx-php/weewx-php). Schema version 1 requires
extension API 1. Packages are separate repositories in this organization.

## Approving a version

1. Review the package's source, dependencies, network targets, options and tests.
   Include a dated review artifact in the package repository. A passing checksum
   check alone is not a code review.
2. Commit the reviewed package. Use its complete 40-character commit SHA.
3. Add or update its record in `catalog.json` through a pull request. Include
   each runtime file, license, manifest and review document with its SHA-256.
   Hash Git blob bytes, including LF line endings, not a transformed download.
4. Run `python3 tools/validate.py`. It validates the catalog and retrieves the
   listed files without executing PHP. The catalog maintainer reviews the PR.

The catalog contains one currently approved release per extension ID. Removing
a record prevents new installation and activation; it does not remotely disable
an already active installation. Administrators can still deactivate and remove it.
Updating requires an explicit administrator action. There are no automatic code
updates. New installations are disabled until activated.

## Record

Each record contains `id`, `name`, `description`, `version` (three-part numeric),
`repository`, `commit`, `entry`, `api`, `php` (minimum version), `requires` (PHP
extensions), `files` (path-to-SHA-256 map), `reviewed_at`, and `review` (a listed
file). The installer only uses fixed HTTPS URLs on `raw.githubusercontent.com`
for the `weewx-php` organization. Links and HTML from catalog strings are not run.

Limits: 200 records, 64 files per package, 512 KiB per file, 4 MiB total per
package. No path traversal, hidden files, duplicate/case-conflicting paths or
mutable branch/tag references. Installation uses individual files, so shared
hosting needs neither ZIP, Git, Composer nor shell execution for the installer.

The catalog maintainers are part of the code trust boundary. Protect `main`,
review changes and secure organization accounts. A reviewed release is not a
guarantee that software has no defects. Technical validation checks integrity;
the linked review records the scope and evidence of the code review.
