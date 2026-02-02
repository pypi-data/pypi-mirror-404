#!/usr/bin/env python3
"""
approval_verifier.py - Approval workflow verification framework
CRITICAL-5 Fix: Approval Bypass Risk (CVSS 7.5)
Created: 2026-01-28 for TASK_204
Purpose: Verify approval workflow integrity and prevent bypass attempts
"""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import sys


class ApprovalVerifier:
    """Verify approval workflow transitions and prevent bypass attempts"""

    # Valid state transitions that REQUIRE approval
    REQUIRES_APPROVAL = {
        'PLANNING': 'AWAITING_APPROVAL',  # Planning -> Must get approval
        'AWAITING_APPROVAL': 'IN_PROGRESS',  # Approval -> Can start work
    }

    # Direct transitions that DON'T require approval (emergency/simple tasks)
    # Format: set of (from_state, to_state) tuples
    ALLOWED_WITHOUT_APPROVAL = {
        ('NEEDS_ACTION', 'PLANNING'),  # Can start planning
        ('NEEDS_ACTION', 'IN_PROGRESS'),  # Simple tasks (Bronze level only)
        ('IN_PROGRESS', 'COMPLETED'),  # Natural completion
        ('COMPLETED', 'DONE'),  # Archival
        ('IN_PROGRESS', 'FAILED'),  # Failure handling
        ('IN_PROGRESS', 'BLOCKED'),  # Blocking issues
        ('BLOCKED', 'IN_PROGRESS'),  # Unblocking
    }

    # Approval timeout windows (by level)
    APPROVAL_TIMEOUTS = {
        'Gold': timedelta(hours=4),  # 4 hours for Gold
        'Silver': timedelta(hours=8),  # 8 hours for Silver
        'Bronze': timedelta(hours=24),  # 24 hours for Bronze
    }

    # Approval timeout extensions for high priority
    PRIORITY_EXTENSIONS = {
        'CRITICAL': timedelta(hours=-2),  # 2 hours faster
        'HIGH': timedelta(hours=-1),  # 1 hour faster
        'MEDIUM': timedelta(hours=0),  # No change
        'LOW': timedelta(hours=4),  # 4 hours slower
    }

    def __init__(self, vault_root: Optional[str] = None):
        """
        Initialize approval verifier

        Args:
            vault_root: Root directory of AI Employee Vault
        """
        self.vault_root = Path(vault_root or '.').resolve()

    def validate_state_transition(
        self,
        from_state: str,
        to_state: str,
        has_approval: bool,
        task_level: str
    ) -> Tuple[bool, str]:
        """
        Validate if a state transition is allowed

        Args:
            from_state: Current state
            to_state: Target state
            has_approval: Whether approval exists
            task_level: Task level (Bronze, Silver, Gold)

        Returns:
            Tuple of (is_valid, reason)
        """
        transition = (from_state, to_state)

        # Check if this transition requires approval
        if from_state in self.REQUIRES_APPROVAL:
            expected_next = self.REQUIRES_APPROVAL[from_state]

            if to_state == expected_next:
                # This is the expected next state after approval
                if not has_approval:
                    return False, f"Transition {from_state} -> {to_state} requires approval"
                return True, "Valid approved transition"
            else:
                # Trying to skip approval workflow
                return False, f"Invalid transition {from_state} -> {to_state}, expected {expected_next}"

        # Check if transition is allowed without approval
        if transition in self.ALLOWED_WITHOUT_APPROVAL:
            return True, "Valid transition (no approval required)"

        # Special case: Bronze-level simple tasks can skip PLANNING
        if task_level == 'Bronze' and from_state == 'NEEDS_ACTION' and to_state == 'IN_PROGRESS':
            return True, "Bronze-level simple task (approval optional)"

        # Unknown or invalid transition
        return False, f"Unknown transition {from_state} -> {to_state}"

    def check_approval_timeout(
        self,
        approval_requested_at: datetime,
        task_level: str,
        priority: str = 'MEDIUM'
    ) -> Tuple[bool, Optional[datetime]]:
        """
        Check if approval request has timed out

        Args:
            approval_requested_at: When approval was requested
            task_level: Task level (Bronze, Silver, Gold)
            priority: Task priority (CRITICAL, HIGH, MEDIUM, LOW)

        Returns:
            Tuple of (is_expired, deadline)
        """
        if task_level not in self.APPROVAL_TIMEOUTS:
            raise ValueError(f"Invalid task level: {task_level}")

        # Calculate timeout window
        base_timeout = self.APPROVAL_TIMEOUTS[task_level]
        priority_adjustment = self.PRIORITY_EXTENSIONS.get(priority, timedelta(hours=0))
        timeout = base_timeout + priority_adjustment

        # Calculate deadline
        deadline = approval_requested_at + timeout

        # Check if expired
        now = datetime.now()
        is_expired = now > deadline

        return is_expired, deadline

    def find_approval_record(
        self,
        task_id: str,
        level: str
    ) -> Optional[Dict[str, any]]:
        """
        Find approval record for a task

        Args:
            task_id: Task ID (e.g., TASK_201)
            level: Task level (Bronze, Silver, Gold)

        Returns:
            Approval record dict or None if not found
        """
        # Check Approvals_<Level>/Granted/ directory
        approvals_dir = self.vault_root / f"Approvals_{level}" / "Granted"

        if not approvals_dir.exists():
            return None

        # Look for approval file
        approval_file = approvals_dir / f"{task_id}_APPROVAL.md"

        if not approval_file.exists():
            return None

        # Parse approval file
        try:
            content = approval_file.read_text(encoding='utf-8')

            # Extract key information
            approval_data = {
                'task_id': task_id,
                'level': level,
                'file_path': str(approval_file),
                'exists': True
            }

            # Extract approval timestamp (format: Approved: YYYY-MM-DD HH:MM:SS)
            timestamp_match = re.search(
                r'Approved:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
                content
            )
            if timestamp_match:
                approval_data['approved_at'] = datetime.strptime(
                    timestamp_match.group(1),
                    '%Y-%m-%d %H:%M:%S'
                )

            # Extract approver
            approver_match = re.search(r'Approver:\s*(.+)', content)
            if approver_match:
                approval_data['approver'] = approver_match.group(1).strip()

            return approval_data

        except Exception as e:
            return None

    def verify_approval_exists(
        self,
        task_id: str,
        level: str
    ) -> Tuple[bool, str]:
        """
        Verify that approval exists for a task

        Args:
            task_id: Task ID (e.g., TASK_201)
            level: Task level (Bronze, Silver, Gold)

        Returns:
            Tuple of (exists, message)
        """
        approval = self.find_approval_record(task_id, level)

        if approval is None:
            return False, f"No approval record found for {task_id}"

        if approval.get('approved_at'):
            approved_time = approval['approved_at'].strftime('%Y-%m-%d %H:%M:%S')
            approver = approval.get('approver', 'Unknown')
            return True, f"Approved by {approver} at {approved_time}"

        return False, f"Approval record exists but incomplete for {task_id}"

    def audit_state_transition(
        self,
        task_id: str,
        from_state: str,
        to_state: str,
        level: str,
        priority: str = 'MEDIUM',
        timestamp: Optional[datetime] = None
    ) -> Dict[str, any]:
        """
        Audit a state transition attempt

        Args:
            task_id: Task ID
            from_state: Current state
            to_state: Target state
            level: Task level
            priority: Task priority
            timestamp: Transition timestamp (default: now)

        Returns:
            Audit result dictionary
        """
        if timestamp is None:
            timestamp = datetime.now()

        audit_result = {
            'task_id': task_id,
            'from_state': from_state,
            'to_state': to_state,
            'level': level,
            'priority': priority,
            'timestamp': timestamp,
            'approved': False,
            'valid': False,
            'reason': '',
            'warnings': []
        }

        # Check if approval exists
        approval = self.find_approval_record(task_id, level)
        has_approval = approval is not None

        if has_approval:
            audit_result['approved'] = True
            audit_result['approval_data'] = approval

            # Check if approval is expired (for AWAITING_APPROVAL state)
            if from_state == 'AWAITING_APPROVAL' and 'approved_at' in approval:
                is_expired, deadline = self.check_approval_timeout(
                    approval['approved_at'],
                    level,
                    priority
                )
                if is_expired:
                    audit_result['warnings'].append(
                        f"Approval expired (deadline: {deadline})"
                    )

        # Validate transition
        is_valid, reason = self.validate_state_transition(
            from_state,
            to_state,
            has_approval,
            level
        )

        audit_result['valid'] = is_valid
        audit_result['reason'] = reason

        return audit_result

    def log_audit_trail(
        self,
        audit_result: Dict[str, any],
        log_file: Optional[str] = None
    ) -> None:
        """
        Log audit trail to file

        Args:
            audit_result: Audit result from audit_state_transition()
            log_file: Log file path (default: Logs_<Level>/Approvals/audit.log)
        """
        if log_file is None:
            level = audit_result['level']
            log_dir = self.vault_root / f"Logs_{level}" / "Approvals"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "approval_audit.log"
        else:
            log_file = Path(log_file)

        # Format log entry
        timestamp = audit_result['timestamp'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        task_id = audit_result['task_id']
        transition = f"{audit_result['from_state']} -> {audit_result['to_state']}"
        status = "ALLOWED" if audit_result['valid'] else "BLOCKED"
        reason = audit_result['reason']

        log_entry = f"[{timestamp}] [{status}] {task_id}: {transition} - {reason}\n"

        # Add warnings
        for warning in audit_result.get('warnings', []):
            log_entry += f"[{timestamp}] [WARN] {task_id}: {warning}\n"

        # Append to log
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)


class ApprovalBypassError(Exception):
    """Raised when approval bypass attempt is detected"""
    pass


def verify_transition(
    task_id: str,
    from_state: str,
    to_state: str,
    level: str,
    priority: str = 'MEDIUM',
    vault_root: Optional[str] = None
) -> bool:
    """
    Verify state transition is allowed (convenience function)

    Args:
        task_id: Task ID
        from_state: Current state
        to_state: Target state
        level: Task level
        priority: Task priority
        vault_root: Vault root directory

    Returns:
        True if transition is allowed

    Raises:
        ApprovalBypassError: If transition is not allowed
    """
    verifier = ApprovalVerifier(vault_root)

    audit_result = verifier.audit_state_transition(
        task_id,
        from_state,
        to_state,
        level,
        priority
    )

    # Log audit trail
    verifier.log_audit_trail(audit_result)

    if not audit_result['valid']:
        raise ApprovalBypassError(
            f"Transition {from_state} -> {to_state} not allowed: {audit_result['reason']}"
        )

    return True


def main():
    """CLI for approval verification testing"""
    import argparse

    parser = argparse.ArgumentParser(
        description='AI Employee Vault - Approval Verifier (CRITICAL-5 Fix)'
    )

    parser.add_argument('action',
                        choices=['verify', 'check-timeout', 'audit', 'test'],
                        help='Action to perform')

    parser.add_argument('--task-id',
                        help='Task ID (e.g., TASK_201)')

    parser.add_argument('--from-state',
                        help='Current state')

    parser.add_argument('--to-state',
                        help='Target state')

    parser.add_argument('--level',
                        choices=['Bronze', 'Silver', 'Gold'],
                        help='Task level')

    parser.add_argument('--priority',
                        choices=['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
                        default='MEDIUM',
                        help='Task priority')

    args = parser.parse_args()

    verifier = ApprovalVerifier()

    if args.action == 'test':
        # Run comprehensive tests
        print("\n" + "=" * 60)
        print("AI Employee Vault - Approval Verifier Test Suite")
        print("CRITICAL-5 Fix: Approval Bypass Prevention")
        print("=" * 60)

        tests_passed = 0
        tests_failed = 0

        # Test 1: Valid transitions without approval
        print("\n[TEST] Transitions Without Approval Required")
        print("-" * 60)

        no_approval_tests = [
            ('NEEDS_ACTION', 'PLANNING', 'Gold', True, "Start planning"),
            ('IN_PROGRESS', 'COMPLETED', 'Gold', True, "Complete task"),
            ('COMPLETED', 'DONE', 'Gold', True, "Archive task"),
            ('IN_PROGRESS', 'BLOCKED', 'Silver', True, "Block task"),
            ('BLOCKED', 'IN_PROGRESS', 'Silver', True, "Unblock task"),
        ]

        for from_st, to_st, level, should_pass, desc in no_approval_tests:
            is_valid, reason = verifier.validate_state_transition(
                from_st, to_st, False, level
            )

            if is_valid == should_pass:
                print(f"[OK] {desc}: {from_st} -> {to_st}")
                tests_passed += 1
            else:
                print(f"[FAIL] {desc}: {from_st} -> {to_st}")
                print(f"       Expected: {should_pass}, Got: {is_valid}")
                print(f"       Reason: {reason}")
                tests_failed += 1

        # Test 2: Transitions requiring approval (should fail without approval)
        print("\n[TEST] Approval Required Transitions (No Approval)")
        print("-" * 60)

        approval_required_tests = [
            ('AWAITING_APPROVAL', 'IN_PROGRESS', 'Gold', False, "Start without approval"),
            ('PLANNING', 'IN_PROGRESS', 'Gold', False, "Skip approval workflow"),
        ]

        for from_st, to_st, level, should_pass, desc in approval_required_tests:
            is_valid, reason = verifier.validate_state_transition(
                from_st, to_st, False, level
            )

            if is_valid == should_pass:
                print(f"[OK] {desc}: BLOCKED ({reason})")
                tests_passed += 1
            else:
                print(f"[FAIL] {desc}: Should be BLOCKED")
                print(f"       Expected: {should_pass}, Got: {is_valid}")
                tests_failed += 1

        # Test 3: Transitions with approval (should succeed)
        print("\n[TEST] Approved Transitions")
        print("-" * 60)

        approved_tests = [
            ('AWAITING_APPROVAL', 'IN_PROGRESS', 'Gold', True, "Start with approval"),
        ]

        for from_st, to_st, level, should_pass, desc in approved_tests:
            is_valid, reason = verifier.validate_state_transition(
                from_st, to_st, True, level
            )

            if is_valid == should_pass:
                print(f"[OK] {desc}: ALLOWED ({reason})")
                tests_passed += 1
            else:
                print(f"[FAIL] {desc}: Should be ALLOWED")
                print(f"       Expected: {should_pass}, Got: {is_valid}")
                tests_failed += 1

        # Test 4: Timeout calculations
        print("\n[TEST] Approval Timeout Calculations")
        print("-" * 60)

        now = datetime.now()
        timeout_tests = [
            ('Gold', 'CRITICAL', now - timedelta(hours=3), True, "Gold CRITICAL (2h window) - expired"),
            ('Gold', 'MEDIUM', now - timedelta(hours=5), True, "Gold MEDIUM (4h window) - expired"),
            ('Silver', 'HIGH', now - timedelta(hours=8), True, "Silver HIGH (7h window) - expired"),
            ('Bronze', 'LOW', now - timedelta(hours=20), False, "Bronze LOW (28h window) - recent"),
        ]

        for level, priority, requested_at, should_expire, desc in timeout_tests:
            is_expired, deadline = verifier.check_approval_timeout(
                requested_at, level, priority
            )

            if is_expired == should_expire:
                status = "EXPIRED" if is_expired else "ACTIVE"
                print(f"[OK] {desc}: {status}")
                tests_passed += 1
            else:
                print(f"[FAIL] {desc}")
                print(f"       Expected expired={should_expire}, Got={is_expired}")
                tests_failed += 1

        # Test 5: Invalid transitions
        print("\n[TEST] Invalid Transitions (Should Block)")
        print("-" * 60)

        invalid_tests = [
            ('COMPLETED', 'PLANNING', 'Gold', False, "Backwards transition"),
            ('DONE', 'IN_PROGRESS', 'Gold', False, "Restart archived task"),
        ]

        for from_st, to_st, level, should_pass, desc in invalid_tests:
            is_valid, reason = verifier.validate_state_transition(
                from_st, to_st, False, level
            )

            if is_valid == should_pass:
                print(f"[OK] {desc}: BLOCKED")
                tests_passed += 1
            else:
                print(f"[FAIL] {desc}: Should be BLOCKED")
                print(f"       Got: {is_valid}")
                tests_failed += 1

        print("\n" + "=" * 60)
        print(f"Tests passed: {tests_passed}/{tests_passed + tests_failed}")
        print(f"Tests failed: {tests_failed}/{tests_passed + tests_failed}")
        print("=" * 60)

        sys.exit(0 if tests_failed == 0 else 1)

    elif args.action == 'verify':
        if not all([args.task_id, args.from_state, args.to_state, args.level]):
            print("[ERR] --task-id, --from-state, --to-state, --level required")
            sys.exit(1)

        audit_result = verifier.audit_state_transition(
            args.task_id,
            args.from_state,
            args.to_state,
            args.level,
            args.priority
        )

        print(f"\n[AUDIT] {args.task_id}: {args.from_state} -> {args.to_state}")
        print(f"  Level: {args.level}")
        print(f"  Priority: {args.priority}")
        print(f"  Approved: {audit_result['approved']}")
        print(f"  Valid: {audit_result['valid']}")
        print(f"  Reason: {audit_result['reason']}")

        if audit_result.get('warnings'):
            for warning in audit_result['warnings']:
                print(f"  [WARN] {warning}")

        # Log audit trail
        verifier.log_audit_trail(audit_result)

        sys.exit(0 if audit_result['valid'] else 1)

    elif args.action == 'check-timeout':
        if not all([args.task_id, args.level]):
            print("[ERR] --task-id, --level required")
            sys.exit(1)

        approval = verifier.find_approval_record(args.task_id, args.level)

        if not approval:
            print(f"[ERR] No approval record found for {args.task_id}")
            sys.exit(1)

        if 'approved_at' not in approval:
            print(f"[ERR] Approval timestamp not found")
            sys.exit(1)

        is_expired, deadline = verifier.check_approval_timeout(
            approval['approved_at'],
            args.level,
            args.priority
        )

        print(f"\n[TIMEOUT CHECK] {args.task_id}")
        print(f"  Approved: {approval['approved_at']}")
        print(f"  Deadline: {deadline}")
        print(f"  Status: {'EXPIRED' if is_expired else 'ACTIVE'}")

        sys.exit(1 if is_expired else 0)

    elif args.action == 'audit':
        if not all([args.task_id, args.level]):
            print("[ERR] --task-id, --level required")
            sys.exit(1)

        exists, message = verifier.verify_approval_exists(args.task_id, args.level)

        print(f"\n[APPROVAL CHECK] {args.task_id}")
        print(f"  {message}")

        sys.exit(0 if exists else 1)


if __name__ == '__main__':
    main()
