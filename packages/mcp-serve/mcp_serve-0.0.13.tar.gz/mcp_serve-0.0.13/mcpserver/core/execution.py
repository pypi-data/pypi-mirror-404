import asyncio
import uuid
import inspect
import json
import traceback
import contextlib
import io
import sys
from fastmcp import Context

def make_async_job(func):
    """
    Decorator: Converts a function into an Async Job.
    Returns: {"job_id": "...", "status": "pending"} immediately.
    Sends: "job_status" (running) -> "job_result" (complete).
    """
    sig = inspect.signature(func)
    is_async = inspect.iscoroutinefunction(func)

    async def wrapper(ctx: Context, *args, **kwargs):
        job_id = str(uuid.uuid4())

        async def background_worker():
            # 1. Notify Start
            await ctx.info(json.dumps({
                "type": "job_status", 
                "job_id": job_id, 
                "status": "running"
            }))

            result = None
            error = None
            captured_stderr = ""

            try:
                # 2. Execution Logic (Capture output to memory, do not stream)
                stdout_buf = io.StringIO()
                stderr_buf = io.StringIO()

                if is_async:
                    with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
                        # Handle Context Injection
                        call_kwargs = kwargs.copy()
                        if "ctx" in sig.parameters: call_kwargs["ctx"] = ctx
                        
                        result = await func(*args, **call_kwargs)
                else:
                    # Sync function helper
                    def run_sync():
                        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
                            call_kwargs = kwargs.copy()
                            if "ctx" in sig.parameters: call_kwargs["ctx"] = ctx
                            return func(*args, **call_kwargs)

                    # Run in thread
                    result = await asyncio.to_thread(run_sync)
                
                captured_stdout = stdout_buf.getvalue()
                captured_stderr = stderr_buf.getvalue()

            except Exception as e:
                error = str(e)
                captured_stderr += f"\nTraceback:\n{traceback.format_exc()}"

            # 3. Construct Final Result
            # If the tool returned a string, we assume it's the result.
            # If it failed, we append the captured stderr to help the Agent debug.
            final_output = result
            
            if error:
                # If python crashed, ensure the error info is passed back
                final_output = f"❌ TOOL CRASH: {error}\n\nLogs:\n{captured_stderr}"

            # 4. Notify Completion
            await ctx.info(json.dumps({
                "type": "job_result",
                "job_id": job_id,
                "status": "failed" if error else "success",
                "output": final_output,
                "error": error
            }))

        # Fire and Forget
        asyncio.create_task(background_worker())

        # Return Ticket
        return json.dumps({
            "job_id": job_id,
            "status": "pending",
            "message": f"Job submitted for {func.__name__}"
        })

    # Fix Signature for FastMCP introspection
    params = list(sig.parameters.values())
    if "ctx" not in sig.parameters:
        ctx_param = inspect.Parameter("ctx", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Context)
        params.insert(0, ctx_param)
    
    wrapper.__signature__ = sig.replace(parameters=params)
    if hasattr(func, "__annotations__"):
        wrapper.__annotations__ = func.__annotations__.copy()
    wrapper.__annotations__["ctx"] = Context
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    
    return wrapper