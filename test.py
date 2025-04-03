import nexcsi
import inspect

# モジュール内の属性と関数を表示
for name in dir(nexcsi):
    if not name.startswith('__'):
        attr = getattr(nexcsi, name)
        if inspect.isfunction(attr) or inspect.isclass(attr):
            print(f"{name}: {type(attr).__name__}")
        else:
            print(f"{name}: {type(attr).__name__}")