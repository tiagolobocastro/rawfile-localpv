import time
import functools


def indent(obj, lvl):
    return "\n".join([(lvl * " ") + line for line in str(obj).splitlines()])


def fmt_timestamp(ts):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def log_grpc_request(func):
    @functools.wraps(func)
    def wrap(self, request, context):
        start = time.time()
        try:
            res = func(self, request, context)
            end = time.time()
            print(
                f"""{fmt_timestamp(end)} => {func.__name__}({{
{indent(request, 2)}
}}) = {{
{indent(res, 2)}
}} <= {fmt_timestamp(end)} // {(end - start) * 1000:.2f}ms"""
            )
            return res
        except Exception as exc:
            ret = (str(context._state.code), context._state.details)
            end = time.time()
            print(
                f"""{fmt_timestamp(end)} => {func.__name__}({{
{indent(request, 2)}
}}) = {ret} <= {fmt_timestamp(end)} // {(end - start) * 1000:.2f}ms
"""
            )
            raise exc

    return wrap
