#!/usr/bin/env python3
"""
path_validator.py - Path validation and sanitization framework
CRITICAL-3 Fix: Path Traversal Vulnerabilities (CVSS 7.5)
Created: 2026-01-27 for TASK_204
Purpose: Prevent directory traversal attacks and validate file paths
"""

import os
import re
from pathlib import Path
from typing import List, Optional
import sys


class PathValidator:
    """Validate and sanitize file paths to prevent directory traversal attacks"""

    # Default allowed base directories for AI Employee Vault
    DEFAULT_ALLOWED_DIRS = [
        'Working_Gold',
        'Working_Silver',
        'Working_Bronze',
        'Archive_Gold',
        'Archive_Silver',
        'Archive_Bronze',
        'Outputs_Gold',
        'Outputs_Silver',
        'Outputs_Bronze',
        'Logs_Gold',
        'Logs_Silver',
        'Logs_Bronze',
        'Planning_Gold',
        'Planning_Silver',
        'Planning_Bronze',
        'Approvals_Gold',
        'Approvals_Silver',
        'Approvals_Bronze',
    ]

    def __init__(self, allowed_base_dirs: Optional[List[str]] = None, vault_root: Optional[str] = None):
        """
        Initialize path validator

        Args:
            allowed_base_dirs: List of allowed base directories (relative to vault root)
            vault_root: Root directory of AI Employee Vault (defaults to current directory)
        """
        self.vault_root = Path(vault_root or os.getcwd()).resolve()

        if allowed_base_dirs is None:
            allowed_base_dirs = self.DEFAULT_ALLOWED_DIRS

        # Convert to absolute paths
        self.allowed_base_dirs = [
            (self.vault_root / base_dir).resolve()
            for base_dir in allowed_base_dirs
        ]

    def is_safe_path(self, file_path: str) -> bool:
        """
        Check if path is within allowed directories

        Args:
            file_path: Path to validate (can be relative or absolute)

        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Resolve to absolute path
            resolved_path = Path(file_path).resolve()

            # Check if path is within any allowed base directory
            for base_dir in self.allowed_base_dirs:
                try:
                    resolved_path.relative_to(base_dir)
                    return True
                except ValueError:
                    continue

            return False

        except (OSError, RuntimeError):
            # Path resolution failed
            return False

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent attacks

        Args:
            filename: Filename to sanitize

        Returns:
            Sanitized filename

        Raises:
            ValueError: If filename is invalid after sanitization
        """
        # Remove path separators
        filename = filename.replace('/', '_').replace('\\', '_')

        # Remove parent directory references
        filename = filename.replace('..', '')

        # Remove null bytes
        filename = filename.replace('\x00', '')

        # Allow only alphanumeric, dash, underscore, dot
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)

        # Ensure not empty
        if not filename:
            raise ValueError("Invalid filename after sanitization")

        # Ensure doesn't start with dot (hidden file)
        if filename.startswith('.'):
            filename = filename[1:]

        # Ensure not too long (255 char limit on most filesystems)
        if len(filename) > 255:
            filename = filename[:255]

        return filename

    def validate_path(self, file_path: str, base_dir: str) -> Path:
        """
        Validate path is safe and within base directory

        Args:
            file_path: Path to validate (should be relative)
            base_dir: Base directory (relative to vault root)

        Returns:
            Validated absolute path

        Raises:
            ValueError: If path is invalid or escapes base directory
        """
        # Convert base_dir to absolute
        base_path = (self.vault_root / base_dir).resolve()

        # Convert file_path to Path object
        path = Path(file_path)

        # Reject absolute paths from user input
        if path.is_absolute():
            raise ValueError(f"Absolute paths not allowed: {file_path}")

        # Construct full path
        full_path = (base_path / path).resolve()

        # Check if within base directory
        try:
            full_path.relative_to(base_path)
        except ValueError:
            raise ValueError(
                f"Path '{file_path}' escapes base directory '{base_dir}'"
            )

        return full_path

    def safe_join(self, base_dir: str, *paths: str) -> Path:
        """
        Safely join paths, ensuring result stays within base directory

        Args:
            base_dir: Base directory (relative to vault root)
            *paths: Path components to join

        Returns:
            Validated absolute path

        Raises:
            ValueError: If resulting path escapes base directory
        """
        # Join all path components
        joined = os.path.join(*paths) if paths else ''

        # Validate the result
        return self.validate_path(joined, base_dir)

    def check_directory_traversal(self, file_path: str) -> bool:
        """
        Check if path contains directory traversal attempts

        Args:
            file_path: Path to check

        Returns:
            True if path contains traversal attempts, False otherwise
        """
        # Check for common traversal patterns
        traversal_patterns = [
            '..',
            '%2e%2e',  # URL encoded ..
            '%252e%252e',  # Double URL encoded ..
            '..%2f',
            '..%5c',
            '%2e%2e/',
            '%2e%2e\\',
        ]

        path_lower = file_path.lower()

        for pattern in traversal_patterns:
            if pattern in path_lower:
                return True

        return False

    def get_safe_task_dir(self, task_id: str, level: str, area: str) -> Path:
        """
        Get safe path for task directory

        Args:
            task_id: Task ID (e.g., TASK_201)
            level: Level (Bronze, Silver, Gold)
            area: Area (Working, Archive, Outputs, etc.)

        Returns:
            Validated absolute path

        Raises:
            ValueError: If inputs are invalid
        """
        # Validate task_id format
        if not re.match(r'^TASK_\d{3}$', task_id):
            raise ValueError(f"Invalid task ID format: {task_id}")

        # Validate level
        if level not in ['Bronze', 'Silver', 'Gold']:
            raise ValueError(f"Invalid level: {level}")

        # Validate area
        valid_areas = ['Working', 'Archive', 'Outputs', 'Logs', 'Planning']
        if area not in valid_areas:
            raise ValueError(f"Invalid area: {area}")

        # Construct safe path
        base_dir = f"{area}_{level}"

        if area == 'Archive':
            return self.validate_path(f"Completed/{task_id}", base_dir)
        else:
            return self.validate_path(task_id, base_dir)


class SecurityError(Exception):
    """Security-related error (e.g., path traversal attempt)"""
    pass


def safe_file_operation(file_path: str, operation: str = 'read', data: str = None, validator: PathValidator = None):
    """
    Safely perform file operation with path validation

    Args:
        file_path: Path to file
        operation: Operation ('read', 'write', 'append')
        data: Data to write (for write/append operations)
        validator: PathValidator instance (creates default if None)

    Returns:
        File contents (for read operation) or None (for write/append)

    Raises:
        SecurityError: If path is unsafe
        IOError: If file operation fails
    """
    if validator is None:
        validator = PathValidator()

    # Validate path
    if not validator.is_safe_path(file_path):
        raise SecurityError(f"Unsafe path: {file_path}")

    # Check for directory traversal
    if validator.check_directory_traversal(file_path):
        raise SecurityError(f"Directory traversal attempt detected: {file_path}")

    # Perform operation
    if operation == 'read':
        with open(file_path, 'r') as f:
            return f.read()
    elif operation == 'write':
        with open(file_path, 'w') as f:
            f.write(data)
        return None
    elif operation == 'append':
        with open(file_path, 'a') as f:
            f.write(data)
        return None
    else:
        raise ValueError(f"Unknown operation: {operation}")


def main():
    """CLI for path validation testing"""
    import argparse

    parser = argparse.ArgumentParser(
        description='AI Employee Vault - Path Validator (CRITICAL-3 Fix)'
    )

    parser.add_argument('action', choices=['validate', 'sanitize', 'test'],
                        help='Action to perform')

    parser.add_argument('path', nargs='?',
                        help='Path to validate or filename to sanitize')

    parser.add_argument('--base-dir',
                        help='Base directory for validation')

    args = parser.parse_args()

    validator = PathValidator()

    if args.action == 'test':
        # Run comprehensive tests
        print("\n" + "=" * 60)
        print("AI Employee Vault - Path Validator Test Suite")
        print("CRITICAL-3 Fix: Path Traversal Prevention")
        print("=" * 60)

        test_cases = [
            # (path, should_pass, description)
            ("Working_Gold/TASK_204/test.txt", True, "Normal path"),
            ("../../../etc/passwd", False, "Directory traversal (../)"),
            ("Working_Gold/../../../etc/passwd", False, "Mixed traversal"),
            ("/etc/passwd", False, "Absolute path"),
            ("Working_Gold/TASK_204/../TASK_203/file.txt", True, "Within allowed (up then down)"),
            ("test%2e%2e/file", False, "URL encoded traversal"),
            ("Working_Gold/TASK_204/./test.txt", True, "Current directory ref"),
            ("", False, "Empty path"),
        ]

        passed = 0
        failed = 0

        for test_path, should_pass, description in test_cases:
            result = validator.is_safe_path(test_path) if test_path else False
            has_traversal = validator.check_directory_traversal(test_path) if test_path else True

            expected_result = should_pass
            actual_result = result and not has_traversal

            if expected_result == actual_result:
                print(f"[OK] {description}")
                print(f"     Path: {test_path}")
                print(f"     Result: {'ALLOWED' if actual_result else 'BLOCKED'}")
                passed += 1
            else:
                print(f"[FAIL] {description}")
                print(f"       Path: {test_path}")
                print(f"       Expected: {'ALLOWED' if expected_result else 'BLOCKED'}")
                print(f"       Got: {'ALLOWED' if actual_result else 'BLOCKED'}")
                failed += 1
            print()

        print("=" * 60)
        print(f"Tests passed: {passed}/{passed + failed}")
        print(f"Tests failed: {failed}/{passed + failed}")
        print("=" * 60)

        sys.exit(0 if failed == 0 else 1)

    elif args.action == 'validate':
        if not args.path:
            print("[ERR] Path required for validation")
            sys.exit(1)

        print(f"[VALIDATE] Checking path: {args.path}")

        # Check if safe
        is_safe = validator.is_safe_path(args.path)
        has_traversal = validator.check_directory_traversal(args.path)

        print(f"  Safe path: {is_safe}")
        print(f"  Has traversal: {has_traversal}")

        if is_safe and not has_traversal:
            print(f"[OK] Path is safe")
            sys.exit(0)
        else:
            print(f"[BLOCKED] Path is unsafe")
            sys.exit(1)

    elif args.action == 'sanitize':
        if not args.path:
            print("[ERR] Filename required for sanitization")
            sys.exit(1)

        print(f"[SANITIZE] Original: {args.path}")

        try:
            sanitized = validator.sanitize_filename(args.path)
            print(f"[OK] Sanitized: {sanitized}")
            sys.exit(0)
        except ValueError as e:
            print(f"[ERR] {e}")
            sys.exit(1)


if __name__ == '__main__':
    main()
