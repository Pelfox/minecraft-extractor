import sys
import pathlib
import argparse
import subprocess


def build_classpath(client_jar: str = "client.jar", libraries_root: str = "libraries") -> str:
    separator = ";" if sys.platform == "win32" else ":"
    root_path = pathlib.Path(libraries_root)

    classpath_items = [client_jar]
    for object in root_path.rglob("*.jar"):
        if not object.is_file():
            continue
        classpath_items.append(str(object))

    return separator.join(classpath_items)


def main() -> None:
    # Simple CLI to interact with client JAR
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--client-path",
        type=str,
        default="client.jar",
        help="Relative path to the downloaded client.jar file."
    )
    parser.add_argument(
        "--libraries-path",
        type=str,
        default="libraries",
        help="Relative path to the downloaded client libraries folder."
    )
    parser.add_argument(
        "action",
        type=str,
        choices=["generate"],
        help="Action that should be performed."
    )
    args = parser.parse_args()

    classpath = build_classpath(args.client_path, args.libraries_path)
    jvm_arguments = [
        "-Dminecraft.launcher.brand=minecraft-extractor",
        "-Dminecraft.launcher.version=1.0.0",
        "-cp",
        classpath,
    ]

    # Some macOS versions require this flag.
    if sys.platform == "darwin":
        jvm_arguments.append("-XstartOnFirstThread")

    exec_command_parts = ["java", *jvm_arguments]
    match args.action:
        case "generate":
            exec_command_parts.append("net.minecraft.client.data.Main")
            exec_command_parts.append("--all")
        case _:
            print(f"Unknown action: {args.action}")
            return

    subprocess.run(exec_command_parts)


if __name__ == "__main__":
    main()
