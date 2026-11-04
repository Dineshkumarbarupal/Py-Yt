"""Promote an existing account to platform administrator.

Run from the repository root:
    python -m scripts.bootstrap_admin --email admin@example.com --confirm
"""
import argparse
import sys

from sqlalchemy import select

from db.models import User
from db.session import SessionLocal


def main() -> int:
    parser = argparse.ArgumentParser(description="Promote an existing Py-Yt user to administrator.")
    parser.add_argument("--email", required=True, help="Existing account email address.")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required acknowledgement that this grants platform-wide administrative access.",
    )
    args = parser.parse_args()

    if not args.confirm:
        parser.error("Pass --confirm after verifying the account email and authorization.")

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == args.email.strip().lower()))
        if not user:
            print("No account exists for that email. Create the account first.", file=sys.stderr)
            return 1
        if user.role == "admin":
            print(f"{user.email} is already an administrator.")
            return 0
        user.role = "admin"
        db.commit()
        print(f"Administrator role granted to {user.email}.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
