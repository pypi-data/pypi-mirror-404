#!/usr/bin/env python3

import argparse
import sys

from gitconfig_cli.ssh import (
    add_ssh_account,
    list_ssh_accounts,
    remove_ssh_account,
    test_ssh_account,
    doctor
)
from gitconfig_cli.git import (
    configure_git_identity,
    use_account
)
from gitconfig_cli.utils import print_banner, error, export_config


def cmd_add(args):
    add_ssh_account(
        provider=args.provider,
        account=args.account,
        email=args.email,
        key_type=args.key_type,
        host=args.host,
        non_interactive=args.non_interactive,
    )


def cmd_list(args):
    list_ssh_accounts()


def cmd_remove(args):
    remove_ssh_account(args.account)


def cmd_git(args):
    configure_git_identity(
        name=args.name,
        email=args.email,
        scope=args.scope,
    )


def cmd_use(args):
    use_account(args.account)


def cmd_test(args):
    test_ssh_account(args.account, verbose=args.verbose)


def cmd_doctor(args):
    doctor()


def cmd_export(args):
    export_config(args.output)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gitconfig",
        description="Git + SSH multi-account configuration CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run without prompts (fail if data missing)",
    )

    sub = parser.add_subparsers(dest="command")

    # ─────────────────────────────────────────────
    # add
    # ─────────────────────────────────────────────
    p_add = sub.add_parser("add", help="Add a new SSH account/key")
    p_add.add_argument("--provider", required=True,
                       help="github | gitlab | bitbucket | custom")
    p_add.add_argument("--account", required=True,
                       help="Account label (e.g. work, personal)")
    p_add.add_argument("--email", required=True,
                       help="Email for SSH key comment")
    p_add.add_argument(
        "--key-type",
        choices=["ed25519", "rsa"],
        default="ed25519",
        help="SSH key type (rsa is legacy)",
    )
    p_add.add_argument(
        "--host",
        default=None,
        help="Custom hostname (defaults to provider domain)",
    )
    p_add.set_defaults(func=cmd_add)

    # ─────────────────────────────────────────────
    # use
    # ─────────────────────────────────────────────
    p_use = sub.add_parser(
        "use",
        help="Use an SSH account for the current repository",
    )
    p_use.add_argument(
        "account",
        help="Account label (e.g. work, personal)",
    )
    p_use.set_defaults(func=cmd_use)

    # ─────────────────────────────────────────────
    # doctor
    # ─────────────────────────────────────────────
    p_doc = sub.add_parser(
        "doctor",
        help="Check SSH environment and permissions",
    )
    p_doc.set_defaults(func=cmd_doctor)

    # ─────────────────────────────────────────────
    # list
    # ─────────────────────────────────────────────
    p_list = sub.add_parser(
        "list",
        aliases=["ls"],
        help="List configured SSH accounts",
    )
    p_list.set_defaults(func=cmd_list)

    # ─────────────────────────────────────────────
    # remove
    # ─────────────────────────────────────────────
    p_rm = sub.add_parser(
        "remove",
        aliases=["rm"],
        help="Remove an SSH account",
    )
    p_rm.add_argument("account", help="Account label to remove")
    p_rm.set_defaults(func=cmd_remove)


    # ─────────────────────────────────────────────
    # test
    # ─────────────────────────────────────────────
    p_test = sub.add_parser(
        "test",
        help="Test SSH connection for an account",
    )
    p_test.add_argument("account", help="Account label to test")
    p_test.set_defaults(func=cmd_test)

    # ─────────────────────────────────────────────
    # export
    # ─────────────────────────────────────────────
    p_exp = sub.add_parser(
        "export",
        help="Export configuration for backup",
    )
    p_exp.add_argument(
        "-o",
        "--output",
        help="Output file (defaults to stdout)",
    )
    p_exp.set_defaults(func=cmd_export)

    # ─────────────────────────────────────────────
    # git
    # ─────────────────────────────────────────────
    p_git = sub.add_parser("git", help="Configure git user identity")
    p_git.add_argument("--name", required=True, help="Git user.name")
    p_git.add_argument("--email", required=True, help="Git user.email")
    p_git.add_argument(
        "--scope",
        choices=["global", "local"],
        default="local",
        help="Apply config globally or to current repo",
    )
    p_git.set_defaults(func=cmd_git)

    return parser


def main(argv=None):
    print_banner()

    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except KeyboardInterrupt:
        error("Interrupted by user")
        sys.exit(130)
    except Exception as e:
        error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
