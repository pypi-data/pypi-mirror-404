#!/usr/bin/env python3
"""
integrity_checker.py - SHA-256 checksum for archives
CRITICAL-6 Fix: No Backup Integrity Verification (CVSS 6.5)
Created: 2026-01-27 for TASK_204
Purpose: Generate and verify SHA-256 checksums for all archived files
"""

import hashlib
import json
from pathlib import Path
from datetime import datetime
import sys
import argparse


class IntegrityChecker:
    """Handle SHA-256 checksum generation and verification for archives"""

    def __init__(self, verbose=True):
        self.verbose = verbose

    def _log(self, message):
        """Print message if verbose mode enabled"""
        if self.verbose:
            print(message)

    def generate_checksum(self, file_path):
        """Generate SHA-256 checksum for a file"""
        sha256 = hashlib.sha256()

        try:
            with open(file_path, 'rb') as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)

            return sha256.hexdigest()

        except Exception as e:
            self._log(f"[ERR] Error generating checksum for {file_path}: {e}")
            return None

    def create_integrity_file(self, archive_dir):
        """Create integrity.json with checksums for all files in archive"""
        archive_path = Path(archive_dir)

        if not archive_path.exists():
            self._log(f"[ERR] Archive directory does not exist: {archive_dir}")
            return None

        self._log(f"\n[SCAN] Scanning archive: {archive_path.name}")
        self._log("=" * 60)

        integrity_data = {
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'archive_dir': str(archive_path.name),
            'files': {}
        }

        file_count = 0
        error_count = 0

        # Scan all files in archive
        for file_path in sorted(archive_path.rglob('*')):
            if file_path.is_file() and file_path.name != 'integrity.json':
                rel_path = str(file_path.relative_to(archive_path))

                checksum = self.generate_checksum(file_path)

                if checksum:
                    integrity_data['files'][rel_path] = {
                        'sha256': checksum,
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(
                            file_path.stat().st_mtime
                        ).isoformat()
                    }
                    self._log(f"[OK] {rel_path}: {checksum[:16]}...")
                    file_count += 1
                else:
                    error_count += 1

        # Save integrity file
        integrity_file = archive_path / 'integrity.json'

        try:
            with open(integrity_file, 'w') as f:
                json.dump(integrity_data, f, indent=2)

            self._log(f"\n[OK] Integrity file created: {integrity_file}")
            self._log(f"   Files processed: {file_count}")
            self._log(f"   Errors: {error_count}")

            return integrity_data

        except Exception as e:
            self._log(f"[ERR] Error saving integrity file: {e}")
            return None

    def verify_integrity(self, archive_dir):
        """Verify all files match stored checksums"""
        archive_path = Path(archive_dir)
        integrity_file = archive_path / 'integrity.json'

        if not integrity_file.exists():
            self._log(f"[ERR] No integrity file found in {archive_dir}")
            return False, ["No integrity.json file found"]

        self._log(f"\n[VERIFY] Verifying integrity: {archive_path.name}")
        self._log("=" * 60)

        try:
            with open(integrity_file, 'r') as f:
                integrity_data = json.load(f)
        except Exception as e:
            self._log(f"[ERR] Error reading integrity file: {e}")
            return False, [f"Cannot read integrity.json: {e}"]

        errors = []
        verified_count = 0
        missing_count = 0
        mismatch_count = 0

        # Verify each file
        for rel_path, file_info in integrity_data['files'].items():
            file_path = archive_path / rel_path

            if not file_path.exists():
                self._log(f"[ERR] Missing: {rel_path}")
                errors.append(f"Missing file: {rel_path}")
                missing_count += 1
                continue

            current_checksum = self.generate_checksum(file_path)

            if current_checksum != file_info['sha256']:
                self._log(f"[ERR] Checksum mismatch: {rel_path}")
                self._log(f"   Expected: {file_info['sha256'][:16]}...")
                self._log(f"   Got:      {current_checksum[:16] if current_checksum else 'ERROR'}...")
                errors.append(f"Checksum mismatch: {rel_path}")
                mismatch_count += 1
            else:
                self._log(f"[OK] {rel_path}")
                verified_count += 1

        # Summary
        self._log("\n" + "=" * 60)
        self._log(f"Verification Summary:")
        self._log(f"  [OK] Verified: {verified_count}")
        self._log(f"  [ERR] Missing: {missing_count}")
        self._log(f"  [ERR] Mismatched: {mismatch_count}")

        success = len(errors) == 0

        if success:
            self._log(f"\n[OK] SUCCESS: All files verified")
        else:
            self._log(f"\n[ERR] FAILED: {len(errors)} integrity issues found")

        return success, errors

    def scan_all_archives(self, base_dir, create=False):
        """Scan all archives in base directory"""
        base_path = Path(base_dir)

        if not base_path.exists():
            self._log(f"[ERR] Base directory does not exist: {base_dir}")
            return

        self._log(f"\n[ARCHIVES] Scanning archives in: {base_path}")
        self._log("=" * 60)

        archives_found = 0
        archives_processed = 0
        archives_failed = 0

        # Find all task archives
        for task_dir in sorted(base_path.glob('TASK_*')):
            if task_dir.is_dir():
                archives_found += 1

                if create:
                    # Create integrity file
                    result = self.create_integrity_file(task_dir)
                    if result:
                        archives_processed += 1
                    else:
                        archives_failed += 1
                else:
                    # Verify integrity
                    success, errors = self.verify_integrity(task_dir)
                    if success:
                        archives_processed += 1
                    else:
                        archives_failed += 1

        # Summary
        self._log("\n" + "=" * 60)
        self._log(f"Archives found: {archives_found}")
        self._log(f"Archives processed: {archives_processed}")
        self._log(f"Archives failed: {archives_failed}")


def main():
    parser = argparse.ArgumentParser(
        description='AI Employee Vault - Backup Integrity Checker (CRITICAL-6 Fix)'
    )

    parser.add_argument(
        'archive_dir',
        nargs='?',
        help='Archive directory to process'
    )

    parser.add_argument(
        '--create',
        action='store_true',
        help='Create integrity.json file'
    )

    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify integrity against integrity.json'
    )

    parser.add_argument(
        '--scan-all',
        metavar='BASE_DIR',
        help='Scan all archives in base directory'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet mode (suppress output)'
    )

    args = parser.parse_args()

    checker = IntegrityChecker(verbose=not args.quiet)

    if args.scan_all:
        # Scan all archives
        checker.scan_all_archives(args.scan_all, create=args.create)

    elif args.archive_dir:
        if args.create:
            # Create integrity file
            result = checker.create_integrity_file(args.archive_dir)
            sys.exit(0 if result else 1)

        elif args.verify:
            # Verify integrity
            success, errors = checker.verify_integrity(args.archive_dir)
            sys.exit(0 if success else 1)

        else:
            print("Error: Must specify --create or --verify")
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
