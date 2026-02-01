import re
import argparse

def bump_version(version_type):
    with open("pyproject.toml", "r") as f:
        content = f.read()

    current_version = re.search(r'^version\s*=\s*"(.*)"', content, re.MULTILINE)
    if not current_version:
        raise ValueError("Version not found in pyproject.toml")
    
    version_parts = list(map(int, current_version.group(1).split('.')))

    if version_type == "major":
        version_parts[0] += 1
        version_parts[1] = 0
        version_parts[2] = 0
    elif version_type == "minor":
        version_parts[1] += 1
        version_parts[2] = 0
    elif version_type == "patch":
        version_parts[2] += 1
    else:
        raise ValueError("Invalid version type. Use 'major', 'minor', or 'patch'.")

    new_version = ".".join(map(str, version_parts))
    updated_content = re.sub(r'(^version\s*=\s*").*(")', r'\g<1>' + new_version + r'\g<2>', content, flags=re.MULTILINE)

    with open("pyproject.toml", "w") as f:
        f.write(updated_content)
    
    print(f"Version bumped from {current_version.group(1)} to {new_version}")
    return new_version

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bump project version in pyproject.toml")
    parser.add_argument("type", choices=["major", "minor", "patch"], default="minor", nargs="?",
                        help="Type of version bump: major, minor, or patch (default: minor)")
    args = parser.parse_args()
    bump_version(args.type)
