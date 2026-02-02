import importlib
import pkgutil
import os
from fastapi import FastAPI, APIRouter

def register_routes(app: FastAPI, package_name: str = "app.http"):
    """
    Automatically discovers and registers routers from the 'app/http' directory.
    """
    print(f"🔍 Scanning for routes in: {package_name}")
    
    try:
        # 1. Find the package path
        package = importlib.import_module(package_name)
        package_path = package.__path__

        # 2. Loop through all files in that folder
        for _, module_name, _ in pkgutil.iter_modules(package_path):
            if module_name == "__init__":
                continue

            # 3. Import the module dynamically (e.g., 'app.http.agents')
            full_module_name = f"{package_name}.{module_name}"
            module = importlib.import_module(full_module_name)

            # 4. Look for a variable named 'router' inside that file
            if hasattr(module, "router") and isinstance(module.router, APIRouter):
                # 5. Register it!
                # Prefix will be the filename (e.g., users.py -> /users)
                prefix = f"/{module_name}"
                app.include_router(module.router, prefix=prefix, tags=[module_name])
                print(f"   ➡ Mounted Route: {prefix}")
            else:
                print(f"   ⚠️ File '{module_name}.py' has no 'router' object. Skipping.")

    except ModuleNotFoundError:
        print(f"⚠️ Could not find route package '{package_name}'. Skipping auto-routing.")
    except Exception as e:
        print(f"❌ Routing Error: {e}")