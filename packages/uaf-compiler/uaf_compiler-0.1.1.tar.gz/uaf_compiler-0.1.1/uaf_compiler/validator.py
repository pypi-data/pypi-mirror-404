import tarfile
import yaml
import io
from .schema import AgentYaml
from pydantic import ValidationError

class UAFValidator:
    def __init__(self, uaf_path: str):
        self.uaf_path = uaf_path

    def validate(self):
        print(f"Validating {self.uaf_path}...")
        if not tarfile.is_tarfile(self.uaf_path):
             raise ValueError(f"{self.uaf_path} is not a valid tar file.")

        with tarfile.open(self.uaf_path, "r:gz") as tar:
            # Check for agent.yaml
            try:
                agent_yaml_info = tar.getmember("agent.yaml")
            except KeyError:
                raise ValueError("Archive is missing 'agent.yaml'")
            
            # Read and validate agent.yaml
            f = tar.extractfile(agent_yaml_info)
            if f is None:
                 raise ValueError("Could not extract agent.yaml")
            
            content = f.read()
            try:
                data = yaml.safe_load(content)
                agent_config = AgentYaml(**data)
                print("  [OK] agent.yaml schema validation passed.")
            except ValidationError as e:
                raise ValueError(f"agent.yaml inside archive is invalid: {e}")
            except yaml.YAMLError as e:
                 raise ValueError(f"agent.yaml inside archive is not valid YAML: {e}")

            # Check entrypoint existence
            entrypoint_file = agent_config.entrypoint.split(":")[0]
            try:
                tar.getmember(entrypoint_file)
                print(f"  [OK] Entrypoint file '{entrypoint_file}' exists in archive.")
            except KeyError:
                raise ValueError(f"CRITICAL: Entrypoint file '{entrypoint_file}' specified in agent.yaml is missing from archive.")

            # Strict: Check requirements.txt
            try:
                tar.getmember("requirements.txt")
                print("  [OK] requirements.txt found.")
            except KeyError:
                print("  [WARNING] requirements.txt is missing. Agent may fail to run without dependencies.")

            # Strict: Validate Tools existence
            if agent_config.tools:
                for tool in agent_config.tools:
                     # Check python tool file
                     if tool.file_path:
                         try:
                            tar.getmember(tool.file_path)
                            print(f"  [OK] Tool implementation '{tool.file_path}' found.")
                         except KeyError:
                             raise ValueError(f"Tool implementation file '{tool.file_path}' for tool '{tool.name}' is missing from archive.")
                     
                     # Check schema file (if exists)
                     if tool.schema_file:
                         try:
                            tar.getmember(tool.schema_file)
                            print(f"  [OK] Tool schema '{tool.schema_file}' found.")
                         except KeyError:
                             raise ValueError(f"Tool schema file '{tool.schema_file}' for tool '{tool.name}' is missing from archive.")

            print("UAF Validation Successful.")
