import tarfile
import yaml
import json

class UAFInspector:
    def __init__(self, uaf_path: str):
        self.uaf_path = uaf_path

    def inspect(self):
        print(f"Inspecting {self.uaf_path}...\n")
        
        if not tarfile.is_tarfile(self.uaf_path):
             print("Error: Not a valid tar file.")
             return

        with tarfile.open(self.uaf_path, "r:gz") as tar:
            print("Contents:")
            for member in tar.getmembers():
                print(f" - {member.name} ({member.size} bytes)")
            
            print("\nMetadata (agent.yaml):")
            try:
                f = tar.extractfile("agent.yaml")
                if f:
                    content = yaml.safe_load(f)
                    print(yaml.dump(content, default_flow_style=False))
            except KeyError:
                print("  Error: agent.yaml not found.")
            except Exception as e:
                print(f"  Error reading agent.yaml: {e}")
