import argparse
import json
import sys

def main():
    parser = argparse.ArgumentParser(description="Repeatable FDM CAD generation and validation")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="Execute trusted model source and validate its exports")
    build.add_argument("--model", required=True)
    build.add_argument("--params", required=True)
    build.add_argument("--output", required=True)
    build.add_argument("--no-previews", action="store_true")
    inspect = commands.add_parser("mesh-inspect", help="Read-only inspection normalized to millimeters")
    inspect.add_argument("file")
    inspect.add_argument("--units", choices=["mm", "cm", "m", "in"])
    args = parser.parse_args()
    try:
        if args.command == "build":
            from .build import build_project
            report = build_project(args.model, args.params, args.output, previews=not args.no_previews)
            print(json.dumps({"status": report["status"], "parts": list(report["parts"]), "output": args.output}, indent=2))
        else:
            from .geometry import mesh_inspect
            print(json.dumps(mesh_inspect(args.file, args.units), indent=2))
    except (ValueError, RuntimeError) as error:
        print(f"CAD error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
