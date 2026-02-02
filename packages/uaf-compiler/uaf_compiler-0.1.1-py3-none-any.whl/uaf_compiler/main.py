import argparse
import sys
import os

# Ensure we can import modules from the current directory if running as a script
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from uaf_compiler.builder import UAFBuilder
from uaf_compiler.validator import UAFValidator
from uaf_compiler.inspector import UAFInspector
from uaf_compiler.loader import UAFLoader

def main():
    parser = argparse.ArgumentParser(description="Universal Agent File (UAF) Compiler")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Build Command
    parser_build = subparsers.add_parser("compile", help="Compile a UAF agent from a setup file")
    parser_build.add_argument("-f", "--setup-file", default="uaf_setup.yaml", help="Path to uaf_setup.yaml (default: uaf_setup.yaml)")

    # Validate Command
    parser_validate = subparsers.add_parser("validate", help="Validate a .uaf file")
    parser_validate.add_argument("file", help="Path to the .uaf file")

    # Inspect Command
    parser_inspect = subparsers.add_parser("inspect", help="Inspect a .uaf file")
    parser_inspect.add_argument("file", help="Path to the .uaf file")

    # Run Command (Test)
    parser_run = subparsers.add_parser("run", help="Run/Load a .uaf file (Test)")
    parser_run.add_argument("file", help="Path to the .uaf file")

    args = parser.parse_args()

    if args.command == "compile":
        try:
            builder = UAFBuilder(args.setup_file)
            builder.build()
        except Exception as e:
            print(f"Build failed: {e}")
            sys.exit(1)
    
    elif args.command == "validate":
        try:
            validator = UAFValidator(args.file)
            validator.validate()
        except Exception as e:
            print(f"Validation failed: {e}")
            sys.exit(1)

    elif args.command == "inspect":
        try:
            inspector = UAFInspector(args.file)
            inspector.inspect()
        except Exception as e:
            print(f"Inspection failed: {e}")
            sys.exit(1)
            
    elif args.command == "run":
        try:
            loader = UAFLoader(args.file)
            agent_factory, meta = loader.load()
            print(f"Successfully loaded agent '{meta.name}' version {meta.version}")
            print(f"Running entrypoint...")
            # Execute the factory
            agent_instance = agent_factory()
            print(f"Result: {agent_instance}")
            # loader.cleanup() # Keep it for inspection if needed, or cleanup
        except Exception as e:
            print(f"Run failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
            
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
