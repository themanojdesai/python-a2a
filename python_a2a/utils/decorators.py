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
        # Set class attributes
        cls_name = name or cls.__name__
        cls.description = description or cls.__doc__ or ""
        cls.version = version or "1.0.0"
        
        # Add additional agent card attributes
        for key, value in kwargs.items():
            setattr(cls, key, value)
            
        # Add helper method to run the agent
        def run(self, host="0.0.0.0", port=5000):
            from ..server import run_server
            run_server(self, host=host, port=port)
            
        cls.run = run
        
        return cls
    
    return decorator