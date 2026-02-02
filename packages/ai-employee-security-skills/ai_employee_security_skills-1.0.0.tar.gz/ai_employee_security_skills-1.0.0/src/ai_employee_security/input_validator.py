#!/usr/bin/env python3
"""
input_validator.py - Input validation framework
CRITICAL-4 Fix: Insufficient Input Validation (CVSS 7.0)
CRITICAL-8 Fix: Sensitive Data in Logs (CVSS 6.0) - Log sanitization
Created: 2026-01-27 for TASK_204
Purpose: Validate all user inputs and sanitize sensitive data
"""

import re
from datetime import datetime
from typing import Any, Dict, Optional
import sys


class InputValidator:
    """Comprehensive input validation for AI Employee Vault"""

    # Task ID format: TASK_###
    TASK_ID_PATTERN = re.compile(r'^TASK_[0-9]{3}$')

    # ISO 8601 with milliseconds: YYYY-MM-DD HH:MM:SS.mmm
    TIMESTAMP_PATTERN = re.compile(
        r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}$'
    )

    # Safe filename characters (alphanumeric, dot, dash, underscore)
    FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._-]+$')

    # Valid task states
    VALID_STATES = [
        'NEEDS_ACTION',
        'PLANNING',
        'AWAITING_APPROVAL',
        'IN_PROGRESS',
        'COMPLETED',
        'DONE',
        'FAILED',
        'BLOCKED'
    ]

    # Valid levels
    VALID_LEVELS = ['Bronze', 'Silver', 'Gold']

    # Valid priorities
    VALID_PRIORITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

    @staticmethod
    def validate_task_id(task_id: str) -> tuple[str, str]:
        """
        Validate task ID format and extract level

        Args:
            task_id: Task ID to validate (e.g., TASK_201)

        Returns:
            Tuple of (task_id, level)

        Raises:
            ValueError: If task ID is invalid
        """
        if not InputValidator.TASK_ID_PATTERN.match(task_id):
            raise ValueError(f"Invalid task ID format: {task_id}")

        # Extract task number
        task_num = int(task_id.split('_')[1])

        # Determine level
        if 1 <= task_num <= 100:
            level = 'Bronze'
        elif 101 <= task_num <= 200:
            level = 'Silver'
        elif 201 <= task_num <= 300:
            level = 'Gold'
        else:
            raise ValueError(f"Task ID {task_id} out of range (must be 001-300)")

        return task_id, level

    @staticmethod
    def validate_timestamp(timestamp_str: str) -> datetime:
        """
        Validate ISO 8601 timestamp with milliseconds

        Args:
            timestamp_str: Timestamp string to validate

        Returns:
            Parsed datetime object

        Raises:
            ValueError: If timestamp is invalid
        """
        if not InputValidator.TIMESTAMP_PATTERN.match(timestamp_str):
            raise ValueError(
                f"Invalid timestamp format: {timestamp_str}. "
                f"Expected: YYYY-MM-DD HH:MM:SS.mmm"
            )

        try:
            dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
            return dt
        except ValueError as e:
            raise ValueError(f"Invalid timestamp: {e}")

    @staticmethod
    def validate_filename(filename: str, max_length: int = 255) -> str:
        """
        Validate filename is safe

        Args:
            filename: Filename to validate
            max_length: Maximum filename length (default: 255)

        Returns:
            Validated filename

        Raises:
            ValueError: If filename is invalid
        """
        if not filename:
            raise ValueError("Filename cannot be empty")

        if len(filename) > max_length:
            raise ValueError(
                f"Filename too long: {len(filename)} chars (max: {max_length})"
            )

        if not InputValidator.FILENAME_PATTERN.match(filename):
            raise ValueError(
                f"Filename contains invalid characters: {filename}. "
                f"Allowed: alphanumeric, dot, dash, underscore"
            )

        # Reject reserved names (Windows)
        reserved = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                    'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                    'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']

        if filename.upper() in reserved:
            raise ValueError(f"Reserved filename: {filename}")

        # Reject filenames starting with dot (hidden files)
        if filename.startswith('.'):
            raise ValueError(f"Filename cannot start with dot: {filename}")

        return filename

    @staticmethod
    def validate_state(state: str) -> str:
        """
        Validate task state

        Args:
            state: State to validate

        Returns:
            Validated state

        Raises:
            ValueError: If state is invalid
        """
        if state not in InputValidator.VALID_STATES:
            raise ValueError(
                f"Invalid state: {state}. "
                f"Valid states: {', '.join(InputValidator.VALID_STATES)}"
            )

        return state

    @staticmethod
    def validate_level(level: str) -> str:
        """
        Validate level

        Args:
            level: Level to validate

        Returns:
            Validated level

        Raises:
            ValueError: If level is invalid
        """
        if level not in InputValidator.VALID_LEVELS:
            raise ValueError(
                f"Invalid level: {level}. "
                f"Valid levels: {', '.join(InputValidator.VALID_LEVELS)}"
            )

        return level

    @staticmethod
    def validate_priority(priority: str) -> str:
        """
        Validate priority

        Args:
            priority: Priority to validate

        Returns:
            Validated priority

        Raises:
            ValueError: If priority is invalid
        """
        if priority not in InputValidator.VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority: {priority}. "
                f"Valid priorities: {', '.join(InputValidator.VALID_PRIORITIES)}"
            )

        return priority

    @staticmethod
    def validate_description(description: str, min_length: int = 10, max_length: int = 1000) -> str:
        """
        Validate task description

        Args:
            description: Description to validate
            min_length: Minimum length (default: 10)
            max_length: Maximum length (default: 1000)

        Returns:
            Validated description

        Raises:
            ValueError: If description is invalid
        """
        if not isinstance(description, str):
            raise ValueError("Description must be a string")

        if len(description) < min_length:
            raise ValueError(
                f"Description too short: {len(description)} chars (min: {min_length})"
            )

        if len(description) > max_length:
            raise ValueError(
                f"Description too long: {len(description)} chars (max: {max_length})"
            )

        return description

    @staticmethod
    def validate_task_specification(spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate complete task specification

        Args:
            spec: Task specification dictionary

        Returns:
            Validated specification

        Raises:
            ValueError: If specification is invalid
        """
        required_fields = ['task_id', 'description', 'level', 'priority']

        # Check required fields
        for field in required_fields:
            if field not in spec:
                raise ValueError(f"Missing required field: {field}")

        # Validate individual fields
        InputValidator.validate_task_id(spec['task_id'])
        InputValidator.validate_description(spec['description'])
        InputValidator.validate_level(spec['level'])
        InputValidator.validate_priority(spec['priority'])

        # Validate optional fields if present
        if 'state' in spec:
            InputValidator.validate_state(spec['state'])

        if 'started' in spec and spec['started']:
            InputValidator.validate_timestamp(spec['started'])

        if 'completed' in spec and spec['completed']:
            InputValidator.validate_timestamp(spec['completed'])

        return spec

    @staticmethod
    def sanitize_log_message(message: str) -> str:
        """
        Sanitize log message to remove sensitive data
        CRITICAL-8 Fix: Sensitive Data in Logs

        Args:
            message: Log message to sanitize

        Returns:
            Sanitized message
        """
        # Patterns to redact (pattern, replacement)
        patterns = [
            # Generic secrets
            (r'(password|passwd|pwd)(\s*[:=]\s*)["\']?([^"\'\s]+)["\']?',
             r'\1\2***', re.IGNORECASE),

            (r'(api[_-]?key|secret|token)(\s*[:=]\s*)["\']?([^"\'\s]+)["\']?',
             r'\1\2***', re.IGNORECASE),

            # Email addresses
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
             '***@***.***', 0),

            # Credit card numbers
            (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
             '****-****-****-****', 0),

            # AWS access keys
            (r'AKIA[0-9A-Z]{16}',
             'AKIA****************', 0),

            # GitHub tokens
            (r'ghp_[A-Za-z0-9]{36}',
             'ghp_***', 0),

            # OpenAI API keys
            (r'sk-[A-Za-z0-9]{48}',
             'sk-***', 0),

            # JWT tokens (base64 strings with dots)
            (r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*',
             'eyJ***.eyJ***.***', 0),

            # IP addresses (optional - may want to keep for debugging)
            # (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '***.***.***.***.***', 0),

            # Social Security Numbers (US)
            (r'\b\d{3}-\d{2}-\d{4}\b',
             '***-**-****', 0),

            # Phone numbers (simple pattern)
            (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
             '***-***-****', 0),
        ]

        sanitized = message

        for pattern, replacement, flags in patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=flags)

        return sanitized


class ValidationError(Exception):
    """Input validation error"""
    pass


def main():
    """CLI for input validation testing"""
    import argparse

    parser = argparse.ArgumentParser(
        description='AI Employee Vault - Input Validator (CRITICAL-4 & CRITICAL-8 Fix)'
    )

    parser.add_argument('action',
                        choices=['test', 'validate-task-id', 'validate-timestamp',
                                 'validate-filename', 'sanitize-log'],
                        help='Action to perform')

    parser.add_argument('value', nargs='?',
                        help='Value to validate or sanitize')

    args = parser.parse_args()

    if args.action == 'test':
        # Run comprehensive tests
        print("\n" + "=" * 60)
        print("AI Employee Vault - Input Validator Test Suite")
        print("CRITICAL-4 & CRITICAL-8 Fixes")
        print("=" * 60)

        tests_passed = 0
        tests_failed = 0

        # Task ID tests
        print("\n[TEST] Task ID Validation")
        print("-" * 60)
        task_id_tests = [
            ("TASK_001", True, "Bronze level"),
            ("TASK_101", True, "Silver level"),
            ("TASK_201", True, "Gold level"),
            ("TASK_999", False, "Out of range"),
            ("TASK_1", False, "Wrong format"),
            ("task_001", False, "Lowercase"),
            ("TASK001", False, "No underscore"),
        ]

        for test_val, should_pass, desc in task_id_tests:
            try:
                InputValidator.validate_task_id(test_val)
                result = True
            except ValueError:
                result = False

            if result == should_pass:
                print(f"[OK] {desc}: {test_val}")
                tests_passed += 1
            else:
                print(f"[FAIL] {desc}: {test_val}")
                tests_failed += 1

        # Timestamp tests
        print("\n[TEST] Timestamp Validation")
        print("-" * 60)
        timestamp_tests = [
            ("2026-01-27 22:50:00.000", True, "Valid timestamp"),
            ("2026-01-27 22:50:00", False, "No milliseconds"),
            ("2026-1-27 22:50:00.000", False, "Single digit month"),
            ("invalid", False, "Invalid format"),
        ]

        for test_val, should_pass, desc in timestamp_tests:
            try:
                InputValidator.validate_timestamp(test_val)
                result = True
            except ValueError:
                result = False

            if result == should_pass:
                print(f"[OK] {desc}: {test_val}")
                tests_passed += 1
            else:
                print(f"[FAIL] {desc}: {test_val}")
                tests_failed += 1

        # Filename tests
        print("\n[TEST] Filename Validation")
        print("-" * 60)
        filename_tests = [
            ("test_file.txt", True, "Valid filename"),
            ("test-file-123.log", True, "Valid with numbers"),
            ("../etc/passwd", False, "Directory traversal"),
            ("test file.txt", False, "Space"),
            (".hidden", False, "Hidden file"),
            ("CON", False, "Reserved name"),
            ("", False, "Empty"),
        ]

        for test_val, should_pass, desc in filename_tests:
            try:
                InputValidator.validate_filename(test_val)
                result = True
            except ValueError:
                result = False

            if result == should_pass:
                print(f"[OK] {desc}: {test_val}")
                tests_passed += 1
            else:
                print(f"[FAIL] {desc}: {test_val}")
                tests_failed += 1

        # Log sanitization tests
        print("\n[TEST] Log Message Sanitization (CRITICAL-8)")
        print("-" * 60)
        sanitization_tests = [
            ("password=secret123", "password=***", "Password redaction"),
            ("api_key=AKIA1234567890123456", "api_key=***", "API key redaction"),
            ("email: user@example.com", "email: ***@***.***", "Email redaction"),
            ("Normal log message", "Normal log message", "No secrets"),
        ]

        for test_val, expected, desc in sanitization_tests:
            sanitized = InputValidator.sanitize_log_message(test_val)
            if expected in sanitized:
                print(f"[OK] {desc}")
                print(f"     Input: {test_val}")
                print(f"     Output: {sanitized}")
                tests_passed += 1
            else:
                print(f"[FAIL] {desc}")
                print(f"       Input: {test_val}")
                print(f"       Expected: {expected}")
                print(f"       Got: {sanitized}")
                tests_failed += 1

        print("\n" + "=" * 60)
        print(f"Tests passed: {tests_passed}/{tests_passed + tests_failed}")
        print(f"Tests failed: {tests_failed}/{tests_passed + tests_failed}")
        print("=" * 60)

        sys.exit(0 if tests_failed == 0 else 1)

    elif args.action == 'validate-task-id':
        if not args.value:
            print("[ERR] Task ID required")
            sys.exit(1)

        try:
            task_id, level = InputValidator.validate_task_id(args.value)
            print(f"[OK] Valid task ID: {task_id}")
            print(f"[OK] Level: {level}")
            sys.exit(0)
        except ValueError as e:
            print(f"[ERR] {e}")
            sys.exit(1)

    elif args.action == 'validate-timestamp':
        if not args.value:
            print("[ERR] Timestamp required")
            sys.exit(1)

        try:
            dt = InputValidator.validate_timestamp(args.value)
            print(f"[OK] Valid timestamp: {args.value}")
            print(f"[OK] Parsed: {dt}")
            sys.exit(0)
        except ValueError as e:
            print(f"[ERR] {e}")
            sys.exit(1)

    elif args.action == 'validate-filename':
        if not args.value:
            print("[ERR] Filename required")
            sys.exit(1)

        try:
            filename = InputValidator.validate_filename(args.value)
            print(f"[OK] Valid filename: {filename}")
            sys.exit(0)
        except ValueError as e:
            print(f"[ERR] {e}")
            sys.exit(1)

    elif args.action == 'sanitize-log':
        if not args.value:
            print("[ERR] Log message required")
            sys.exit(1)

        sanitized = InputValidator.sanitize_log_message(args.value)
        print(f"[INPUT] {args.value}")
        print(f"[OUTPUT] {sanitized}")
        sys.exit(0)


if __name__ == '__main__':
    main()
