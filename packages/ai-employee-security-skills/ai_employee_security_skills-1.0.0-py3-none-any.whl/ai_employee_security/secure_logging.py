#!/usr/bin/env python3
"""
secure_logging.py - Secure logging wrapper with automatic sanitization
CRITICAL-8 Fix: Sensitive Data in Logs (CVSS 6.0)
Created: 2026-01-28 for TASK_204
Purpose: Provide secure logging that automatically sanitizes sensitive data
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Import sanitization function from input_validator
try:
    from input_validator import InputValidator
except ImportError:
    # If running standalone, import from same directory
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from input_validator import InputValidator


class SanitizingFormatter(logging.Formatter):
    """Custom formatter that sanitizes log messages before output"""

    def format(self, record):
        """
        Format log record with sanitization

        Args:
            record: LogRecord to format

        Returns:
            Formatted and sanitized log message
        """
        # Get the original formatted message
        original_message = super().format(record)

        # Sanitize the message
        sanitized_message = InputValidator.sanitize_log_message(original_message)

        return sanitized_message


class SecureLogger:
    """
    Wrapper for Python logging with automatic sanitization

    Usage:
        logger = SecureLogger('my_component')
        logger.info('Processing user password=secret123')  # Automatically sanitized
        logger.error('API key: AKIA1234567890123456')  # Automatically sanitized
    """

    def __init__(
        self,
        name: str,
        log_file: Optional[str] = None,
        level: int = logging.INFO,
        console: bool = True
    ):
        """
        Initialize secure logger

        Args:
            name: Logger name (usually component/module name)
            log_file: Optional log file path
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console: Whether to also log to console
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers = []  # Clear any existing handlers

        # Create sanitizing formatter
        formatter = SanitizingFormatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Add file handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Add console handler if requested
        if console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def debug(self, message: str, *args, **kwargs):
        """Log debug message (automatically sanitized)"""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log info message (automatically sanitized)"""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log warning message (automatically sanitized)"""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log error message (automatically sanitized)"""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log critical message (automatically sanitized)"""
        self.logger.critical(message, *args, **kwargs)


def get_secure_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console: bool = True
) -> SecureLogger:
    """
    Factory function to create secure logger

    Args:
        name: Logger name
        log_file: Optional log file path
        level: Logging level
        console: Whether to log to console

    Returns:
        SecureLogger instance
    """
    return SecureLogger(name, log_file, level, console)


def sanitize_and_log(message: str, level: str = 'INFO', logger_name: str = 'default') -> str:
    """
    Sanitize and log a message (convenience function)

    Args:
        message: Message to sanitize and log
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logger_name: Logger name

    Returns:
        Sanitized message
    """
    logger = get_secure_logger(logger_name, console=True)

    sanitized = InputValidator.sanitize_log_message(message)

    level_func = getattr(logger, level.lower(), logger.info)
    level_func(sanitized)

    return sanitized


def main():
    """CLI for secure logging testing"""
    import argparse

    parser = argparse.ArgumentParser(
        description='AI Employee Vault - Secure Logging (CRITICAL-8 Fix)'
    )

    parser.add_argument('action', choices=['test', 'sanitize'],
                        help='Action to perform')

    parser.add_argument('message', nargs='?',
                        help='Message to sanitize')

    parser.add_argument('--level',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO',
                        help='Log level')

    parser.add_argument('--log-file',
                        help='Log file path')

    args = parser.parse_args()

    if args.action == 'test':
        # Run comprehensive tests
        print("\n" + "=" * 60)
        print("AI Employee Vault - Secure Logging Test Suite")
        print("CRITICAL-8 Fix: Sensitive Data in Logs")
        print("=" * 60)

        # Create test logger
        test_log_file = 'test_secure_logging.log'
        logger = get_secure_logger('test', log_file=test_log_file, console=True)

        print("\n[TEST] Logging Sensitive Data (Should Be Sanitized)")
        print("-" * 60)

        # Test cases
        test_messages = [
            ("User login with password=secret123", "password=***"),
            ("API key: AKIA1234567890123456", "AKIA****************"),
            ("Contact: user@example.com", "***@***.***"),
            ("Token: ghp_abcdefghijklmnopqrstuvwxyz123456", "ghp_***"),
            ("Normal log message with no secrets", "Normal log message with no secrets"),
            ("Credit card: 4532-1234-5678-9010", "****-****-****-****"),
            ("OpenAI key sk-proj-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOP", "sk-***"),
        ]

        tests_passed = 0
        tests_failed = 0

        for original, expected_contains in test_messages:
            print(f"\n[TEST] Original: {original}")

            # Log the message (it will be sanitized)
            logger.info(original)

            # Read back from log file to verify
            with open(test_log_file, 'r', encoding='utf-8') as f:
                log_contents = f.read()

            # Check if sanitization worked
            if expected_contains in log_contents:
                print(f"[OK] Sanitized correctly (contains: {expected_contains})")
                tests_passed += 1
            else:
                print(f"[FAIL] Expected to contain: {expected_contains}")
                print(f"       Log contents: {log_contents[-200:]}")
                tests_failed += 1

            # Clear log file for next test
            open(test_log_file, 'w').close()

        print("\n" + "=" * 60)
        print(f"Tests passed: {tests_passed}/{tests_passed + tests_failed}")
        print(f"Tests failed: {tests_failed}/{tests_passed + tests_failed}")
        print("=" * 60)

        # Close logger handlers before cleanup
        for handler in logger.logger.handlers[:]:
            handler.close()
            logger.logger.removeHandler(handler)

        # Clean up test log file
        import os
        if os.path.exists(test_log_file):
            try:
                os.remove(test_log_file)
            except PermissionError:
                print(f"[WARN] Could not delete {test_log_file} (file in use)")

        sys.exit(0 if tests_failed == 0 else 1)

    elif args.action == 'sanitize':
        if not args.message:
            print("[ERR] Message required for sanitization")
            sys.exit(1)

        # Sanitize and log the message
        sanitized = sanitize_and_log(
            args.message,
            level=args.level,
            logger_name='cli'
        )

        print(f"\n[ORIGINAL] {args.message}")
        print(f"[SANITIZED] {sanitized}")

        sys.exit(0)


if __name__ == '__main__':
    main()
