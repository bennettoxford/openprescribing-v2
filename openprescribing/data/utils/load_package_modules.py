import importlib
import pkgutil


def load_all_modules_with_function(path, name, function_name):
    functions = {}
    for m in pkgutil.walk_packages(path=path):
        mod = importlib.import_module(name + "." + m.name)
        functions[m.name] = getattr(mod, function_name)
    return functions
