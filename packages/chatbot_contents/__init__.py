# chatbot_contents/__init__.py
import pkgutil, importlib

__all__ = []

for finder, module_name, is_pkg in pkgutil.iter_modules(__path__):
    module = importlib.import_module(f"{__name__}.{module_name}")
    for attr in dir(module):
        obj = getattr(module, attr)
        # Content 모델만 골라서 등록 (여기선 클래스명 끝에 "Content" 가 붙은 것들)
        if isinstance(obj, type) and attr.endswith("Content"):
            globals()[attr] = obj
            __all__.append(attr)
            # print(f"  - {attr} 등록")