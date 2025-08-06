import os
import yaml
from jinja2 import Template
import json
from utils.bedrock_utils import call_llm

class MCPWorkflow:
    def __init__(self, manifests_dir="mcp_manifests"):
        self.manifests_dir = manifests_dir
        self.manifests = {}
        self.load_manifests()
        self.context = {}
        self.current_step = None

    def load_manifests(self):
        for file in os.listdir(self.manifests_dir):
            if file.endswith(".mcp.yml"):
                path = os.path.join(self.manifests_dir, file)
                with open(path, "r", encoding="utf-8") as f:
                    manifest = yaml.safe_load(f)
                    self.manifests[manifest["step"]] = manifest

    def start(self, step_name="create_defect", initial_context=None):
        self.current_step = step_name
        if initial_context:
            self.context.update(initial_context)

    def get_current_manifest(self):
        return self.manifests.get(self.current_step)

    def generate_prompt(self):
        manifest = self.get_current_manifest()
        if not manifest:
            raise ValueError(f"Step {self.current_step} not found in manifests")

        template_str = manifest["llm_prompt_template"]
        template = Template(template_str)
        prompt = template.render(context=self.context, allowed_next_steps=manifest.get("allowed_next_steps", []))
        return prompt

    def update_context(self, new_data: dict):
        self.context.update(new_data)

    def proceed_to_next(self, next_step):
        if next_step not in self.manifests:
            raise ValueError(f"Next step '{next_step}' not found in manifests")
        self.current_step = next_step

    def get_input_requirements(self):
        manifest = self.get_current_manifest()
        return manifest.get("input_required", [])
    
    def enrich_context_with_similarity(self, user_text: str, top_k=3):
        from utils.semantic_utils import search_similar_defects

        similar_defects = search_similar_defects(user_text, top_k=top_k)
        self.context["similar_defects"] = similar_defects
    # from utils.bedrock_utils import call_llm  # updated import
    
    def suggest_next_step(self) -> str:
        manifest = self.get_current_manifest()
        allowed_steps = manifest.get("allowed_next_steps", [])
        context_str = json.dumps(self.context, indent=2)

        prompt = f"""
        You are a workflow assistant. The user is currently in step: {self.current_step}.
        Context so far:
        {context_str}

        Allowed next steps: {allowed_steps}

        Based on the current information, what is the most logical next step?
        Respond with only the step name (e.g., 'assign_defect').
        """

        next_step = call_llm(prompt)
        return next_step.strip()



