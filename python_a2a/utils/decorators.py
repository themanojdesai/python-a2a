"""
Decorators for creating A2A agents and skills.
"""

def skill(name, description=None, tags=None, examples=None):
    """Decorator to register a method as an A2A skill"""
    
    def decorator(func):
        # Extract info from function
        func_name = func.__name__
        func_doc = func.__doc__ or ""
        
        # Parse examples from docstring if not provided
        parsed_examples = []
        if examples is None and "Examples:" in func_doc:
            example_section = func_doc.split("Examples:", 1)[1]
            parsed_examples = [
                line.strip().strip('"`\'')
                for line in example_section.split("\n") 
                if line.strip()
            ]
        
        # Construct skill info
        skill_info = {
            "id": func_name,
            "name": name or func_name.replace("_", " ").title(),
            "description": description or func_doc.split("\n\n")[0].strip(),
            "tags": tags or [],
            "examples": examples or parsed_examples
        }
        
        # Attach skill info to the function
        func._skill_info = skill_info
        return func
    
    return decorator


def agent(name, description=None, version=None, **kwargs):
    """Decorator to create an A2A agent class"""
    
    def decorator(cls):
        # Store original __init__ method
        original_init = cls.__init__
        
        # Define a new __init__ that will collect skills and set up the agent card
        def new_init(self, *args, **kwargs):
            # Call original __init__ first
            original_init(self, *args, **kwargs)
            
            # Import here to avoid circular imports
            from ..models.agent import AgentSkill, AgentCard
            
            # Collect skills from decorated methods
            skills = []
            for attr_name in dir(self):
                if attr_name.startswith('__'):
                    continue
                    
                attr = getattr(self, attr_name)
                if callable(attr) and hasattr(attr, '_skill_info'):
                    skill_info = attr._skill_info
                    skills.append(AgentSkill(
                        id=skill_info["id"],
                        name=skill_info["name"],
                        description=skill_info["description"],
                        tags=skill_info["tags"],
                        examples=skill_info["examples"]
                    ))
            
            # Create agent card with collected skills
            self.agent_card = AgentCard(
                name=name or cls.__name__,
                description=description or cls.__doc__ or "",
                url=kwargs.get("url", getattr(self, "url", None)),
                version=version or "1.0.0",
                skills=skills
            )
        
        # Replace __init__ with our new version
        cls.__init__ = new_init
        
        # Set class attributes
        cls.name = name or cls.__name__
        cls.description = description or cls.__doc__ or ""
        cls.version = version or "1.0.0"
        
        # Add additional agent card attributes
        for key, value in kwargs.items():
            setattr(cls, key, value)
            
        # Add helper method to run the agent
        def run(self, host="0.0.0.0", port=None):
            from ..server import run_server
            
            # Use the provided port or let run_server use its default
            if port is not None:
                run_server(self, host=host, port=port)
            else:
                run_server(self, host=host)
            
        cls.run = run
        
        return cls
    
    return decorator