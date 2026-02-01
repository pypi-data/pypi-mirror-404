import functools

class cached_async_property:
    def __init__(self, func):
        self.func = func
        self.attr_name = f"_cached_{func.__name__}"
        functools.update_wrapper(self, func)

    def __get__(self, instance, owner):
        if instance is None:
            return self

        async def wrapper():
            if not hasattr(instance, self.attr_name):
                value = await self.func(instance)
                setattr(instance, self.attr_name, value)
            return getattr(instance, self.attr_name)

        return wrapper()
