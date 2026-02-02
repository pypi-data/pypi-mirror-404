import os
import yaml
import tarfile
from .schema import AgentYaml
from pydantic import ValidationError

class UAFBuilder:
    def __init__(self, setup_file: str):
        self.setup_file = setup_file
        self.base_dir = os.path.dirname(os.path.abspath(setup_file))

    def load_config(self):
        if not os.path.exists(self.setup_file):
            raise FileNotFoundError(f"Setup file not found: {self.setup_file}")
        
        with open(self.setup_file, 'r') as f:
            return yaml.safe_load(f)

    def validate_agent_yaml(self, agent_yaml_path):
        if not os.path.exists(agent_yaml_path):
            raise FileNotFoundError(f"agent.yaml not found at {agent_yaml_path}")
        
        with open(agent_yaml_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
                AgentYaml(**data)
                print("  [OK] agent.yaml validation passed.")
            except ValidationError as e:
                raise ValueError(f"agent.yaml validation failed: {e}")
            except yaml.YAMLError as e:
                 raise ValueError(f"agent.yaml is not valid YAML: {e}")

    def build(self):
        config = self.load_config()
        output_filename = config.get('output', 'agent.uaf')
        files_mapping = config.get('files', {})
        
        # Determine strict validation preference? For now, we strict validate agent.yaml
        
        # Check if 'agent.yaml' is in the mapping, as it is required
        agent_yaml_source = None
        for target_name, source_path in files_mapping.items():
            if target_name == 'agent.yaml':
                agent_yaml_source = source_path if os.path.isabs(source_path) else os.path.join(self.base_dir, source_path)
                break
        
        if not agent_yaml_source:
             raise ValueError("uaf_setup.yaml must include a mapping for 'agent.yaml'")

        print(f"Validating {agent_yaml_source}...")
        self.validate_agent_yaml(agent_yaml_source)

        output_path = os.path.join(self.base_dir, output_filename)
        print(f"Building {output_filename}...")
        
        with tarfile.open(output_path, "w:gz") as tar:
            for target_name, source_rel_path in files_mapping.items():
                source_path = os.path.join(self.base_dir, source_rel_path)
                if not os.path.exists(source_path):
                    # Try raw path just in case
                    if os.path.exists(source_rel_path):
                         source_path = source_rel_path
                    else:
                        raise FileNotFoundError(f"Source file {source_rel_path} for {target_name} not found.")
                
                print(f"  Adding {target_name} from {source_rel_path}")
                tar.add(source_path, arcname=target_name)
        
        print(f"Successfully created {output_path}")
