import importlib
from typing import List, Type
from pathlib import Path

def load_resolver_class(path: str) -> Type:
    """
    Dynamically load a resolver class from a given path.
    
    Args:
        path (str): The full path to the resolver class
        
    Returns:
        Type: The loaded resolver class
        
    Raises:
        ValueError: If the path is not properly formatted (must contain at least one dot)
    """
    if '.' not in path:
        raise ValueError(f"Invalid path format: {path}. Path must be in format 'module.class'")
    
    module_path, class_name = path.rsplit('.', 1)
    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except ImportError as e:
        raise ImportError(f"Could not import module '{module_path}': {str(e)}")
    except AttributeError as e:
        raise AttributeError(f"Could not find class '{class_name}' in module '{module_path}': {str(e)}")

def discover_resolvers(base_path: str = "app/graphql") -> List[str]:
    """
    Discover all resolver classes in the specified base path.
    Looks for files ending with '_query_resolvers.py' and '_mutation_resolvers.py'.
    
    Args:
        base_path (str): The base path to start searching for resolvers
        
    Returns:
        List[str]: List of fully qualified resolver class paths
    """
    query_resolver_paths = []
    mutation_resolver_paths = []
    base = Path(base_path)
    
    # Walk through all subdirectories in the graphql folder
    for path in base.rglob("*_query_resolvers.py"):
        try:
            # Find the position of 'app' in the path
            module_parts = path.parts
            app_index = module_parts.index('app')
            # Take the path from 'app' onwards
            module_path = '.'.join(module_parts[app_index:-1] + (module_parts[-1][:-3],))
            
            # Import the module using importlib
            module = importlib.import_module(module_path)
            
            # Look for classes that end with 'QueryResolver'
            for name, obj in module.__dict__.items():
                if isinstance(obj, type) and name.endswith('QueryResolvers'):
                    query_resolver_paths.append(f"{module_path}.{name}")
        except Exception as e:
            print(f"Error loading query resolver module {str(path)}: {str(e)}")
            continue

    # Walk through all subdirectories looking for mutation resolvers
    for path in base.rglob("*_mutation_resolvers.py"):
        try:
            module_parts = path.parts
            app_index = module_parts.index('app')
            module_path = '.'.join(module_parts[app_index:-1] + (module_parts[-1][:-3],))
            
            module = importlib.import_module(module_path)
            
            # Look for classes that end with 'MutationResolver'
            for name, obj in module.__dict__.items():
                if isinstance(obj, type) and name.endswith('MutationResolvers'):
                    mutation_resolver_paths.append(f"{module_path}.{name}")
        except Exception as e:
            print(f"Error loading mutation resolver module {str(path)}: {str(e)}")
            continue
    
    return [query_resolver_paths, mutation_resolver_paths]