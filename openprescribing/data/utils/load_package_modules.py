import importlib
import pkgutil


def load_all_modules_with_function(path, name, function_name):
    helpers = {}
    for m in pkgutil.walk_packages(path=path):
        mod = importlib.import_module(name + "." + m.name)
        helpers[m.name] = getattr(mod, function_name)
    return helpers
