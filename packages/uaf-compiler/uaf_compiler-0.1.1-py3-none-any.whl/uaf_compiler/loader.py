import tarfile
import yaml
import sys
import os
import importlib.util
import shutil
import tempfile
from .schema import AgentYaml

class UAFLoader:
    def __init__(self, uaf_path: str):
        self.uaf_path = uaf_path
        self.agent_dir = tempfile.mkdtemp(prefix="uaf_agent_")
        self.meta = None

    def load_factory(self):
        """
        Loads the agent source and returns the factory function.
        Call the factory function with arguments to get the runnable agent.
        """
        if not os.path.exists(self.agent_dir) or not os.listdir(self.agent_dir):
             self._extract()

        # Add to path if not already there
        if self.agent_dir not in sys.path:
            sys.path.insert(0, self.agent_dir)
        
        # Load Entrypoint
        if not self.meta:
            self._load_metadata()

        # entrypoint format: module:function
        try:
            module_name, func_name = self.meta.entrypoint.split(":")
        except ValueError:
            raise ValueError(f"Invalid entrypoint format: {self.meta.entrypoint}. Expected module:function")
            
        module_path = os.path.join(self.agent_dir, module_name if module_name.endswith(".py") else f"{module_name}.py")
        
        if not os.path.exists(module_path):
             raise ValueError(f"Entrypoint module {module_path} not found.")

        try:
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            raise ImportError(f"Failed to import agent module: {e}")
        
        if not hasattr(module, func_name):
            raise ValueError(f"Function {func_name} not found in {module_name}")
            
        factory = getattr(module, func_name)
        return factory

    def load(self, **kwargs):
        """
        High-level API to load and instantiate the agent.
        
        Args:
            **kwargs: Dependencies to inject into the agent factory (e.g., llm=...).
            
        Returns:
            The instantiated agent node/graph.
        """
        factory = self.load_factory()
        return factory(**kwargs)

    def _extract(self):
        print(f"Loading agent from {self.uaf_path} into {self.agent_dir}...")
        with tarfile.open(self.uaf_path, "r:gz") as tar:
            tar.extractall(path=self.agent_dir)
        self._load_metadata()

    def _load_metadata(self):
        agent_yaml_path = os.path.join(self.agent_dir, "agent.yaml")
        if not os.path.exists(agent_yaml_path):
             raise ValueError("agent.yaml missing in archive")
        
        with open(agent_yaml_path, "r") as f:
            self.meta = AgentYaml(**yaml.safe_load(f))

    def cleanup(self):
        shutil.rmtree(self.agent_dir)
