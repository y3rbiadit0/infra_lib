import sys
from pathlib import Path

from .infra_generator import InfraGenerator

def main():
    if len(sys.argv) != 3 or sys.argv[1] != "build":
        print("Usage: aws_infra build <stack_type>")
        sys.exit(1)

    stack_type = sys.argv[2]
    project_name = f"my_{stack_type}_project"
    project_dir = Path(".") / project_name
    project_dir.mkdir(exist_ok=True)

    generator = InfraGenerator(project_dir, project_name, stack_type)
    generator.generate()

if __name__ == "__main__":
    main()
