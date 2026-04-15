#!/usr/bin/env python3

import argparse
import re
import subprocess
import sys
from pathlib import Path


VERSION_PATTERN = re.compile(r'version\s*=\s*"(\d+)\.(\d+)\.(\d+)"')


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Bump the package version and optionally commit/tag it."
	)
	parser.add_argument(
		"version_type",
		nargs="?",
		choices=["major", "minor", "patch"],
		default="patch",
		help="Version segment to bump.",
	)
	parser.add_argument(
		"--pyproject-path",
		default="pyproject.toml",
		help="Path to pyproject.toml.",
	)
	parser.add_argument(
		"--version-file-path",
		default="src/infra_lib/cli/__version__.py",
		help="Path to the __version__.py file.",
	)
	parser.add_argument(
		"--yes",
		action="store_true",
		help="Skip the confirmation prompt before formatting, committing, and tagging.",
	)
	parser.add_argument(
		"--dry-run",
		action="store_true",
		help="Print the next version without modifying files.",
	)
	return parser.parse_args()


def get_current_version(pyproject_path: Path) -> tuple[int, int, int, str]:
	content = pyproject_path.read_text(encoding="utf-8")
	match = VERSION_PATTERN.search(content)
	if match is None:
		raise RuntimeError(f"Could not find a version in {pyproject_path}")

	major, minor, patch = (int(part) for part in match.groups())
	return major, minor, patch, content


def increment_version(major: int, minor: int, patch: int, version_type: str) -> str:
	if version_type == "major":
		major += 1
		minor = 0
		patch = 0
	elif version_type == "minor":
		minor += 1
		patch = 0
	else:
		patch += 1

	return f"{major}.{minor}.{patch}"


def update_version_files(
	new_version: str,
	pyproject_path: Path,
	version_file_path: Path,
	pyproject_content: str,
) -> None:
	new_content, replacements = VERSION_PATTERN.subn(
		f'version = "{new_version}"', pyproject_content, count=1
	)
	if replacements != 1:
		raise RuntimeError(f"Could not update version in {pyproject_path}")

	pyproject_path.write_text(new_content, encoding="utf-8")
	print(f"Updated {pyproject_path} to {new_version}")

	if version_file_path.exists():
		version_file_path.write_text(f'__version__ = "{new_version}"\n', encoding="utf-8")
		print(f"Updated {version_file_path} to {new_version}")
	else:
		print(f"Warning: {version_file_path} not found. Skipping.")


def run_command(command: list[str]) -> None:
	subprocess.run(command, check=True)


def format_code() -> None:
	print("Running Ruff format...")
	run_command(["uv", "run", "ruff", "format", "."])


def apply_changes(new_version: str, files_to_commit: list[Path]) -> None:
	file_args = [str(path) for path in files_to_commit]
	run_command(["git", "add", *file_args])
	run_command(["git", "commit", "-m", f"New Release v{new_version}"])
	run_command(["git", "tag", f"v{new_version}"])
	print(f"Committed and tagged version v{new_version}")


def should_apply_changes(new_version: str, auto_confirm: bool) -> bool:
	if auto_confirm:
		return True

	confirmation = input(
		f"Are you sure you want to commit and tag version {new_version}? (y/n) "
	).strip()
	return confirmation.lower() == "y"


def main() -> int:
	args = parse_args()
	pyproject_path = Path(args.pyproject_path)
	version_file_path = Path(args.version_file_path)

	try:
		major, minor, patch, pyproject_content = get_current_version(pyproject_path)
		new_version = increment_version(major, minor, patch, args.version_type)
		print(f"Bumping {args.version_type} version -> {new_version}")

		if args.dry_run:
			print("Dry run: no files were modified.")
			return 0

		update_version_files(new_version, pyproject_path, version_file_path, pyproject_content)

		if should_apply_changes(new_version, args.yes):
			format_code()
			apply_changes(new_version, [pyproject_path, version_file_path])
		else:
			print("Operation cancelled.")

		print("Done. Version bumped, files updated, and code formatted.")
		return 0
	except Exception as exc:
		print(exc, file=sys.stderr)
		return 1


if __name__ == "__main__":
	raise SystemExit(main())
