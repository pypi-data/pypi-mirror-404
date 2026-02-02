"""Concierge SDK - Structured AI workflows with staged tool execution"""
from __future__ import annotations

import asyncio
import os
import subprocess
import time
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable, List, Dict, Optional

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Context

from concierge.backends.vanilla_backend import VanillaBackend
from concierge.core.widget import Widget, WidgetMode
from concierge.telemetry import metrics, ENABLED as METRICS_ENABLED

# Lazy import for raw Server detection (avoid import errors if mcp.server.Server moves)
def _is_raw_server(obj: Any) -> bool:
    """Check if obj is a raw mcp.server.Server (not FastMCP)."""
    try:
        from mcp.server import Server as RawServer
        return isinstance(obj, RawServer) and not isinstance(obj, FastMCP)
    except ImportError:
        return False

_task_session_map: Dict[int, str] = {}

def _get_current_session_id() -> Optional[str]:
    """Get the session ID for the current asyncio task."""
    task = asyncio.current_task()
    if task:
        return _task_session_map.get(id(task))
    return None


class ProviderType(Enum):
    PLAIN = "plain"
    SEARCH = "search"


def _get_provider_class(provider_type: ProviderType):
    """Lazy load provider to avoid importing optional dependencies."""
    if provider_type == ProviderType.SEARCH:
        from concierge.backends.search_backend import SearchBackend
        return SearchBackend
    return VanillaBackend


class Config:
    def __init__(self, max_results=5, provider_type=ProviderType.PLAIN, model=None):
        self.max_results = max_results
        self.provider_type = provider_type
        self.model = model


# Template for Mode 2 (URL → iframe wrapper)
IFRAME_TEMPLATE = '''<!DOCTYPE html>
<html>
<head><style>*{margin:0;padding:0}iframe{width:100%;height:100vh;border:none}</style></head>
<body><iframe src="{url}"></iframe></body>
</html>'''


class Concierge:

    def __init__(self, server, *, config=Config(), assets_dir: Optional[str] = None, **fastmcp_kwargs):
        # Detect server type and wrap appropriately
        if isinstance(server, FastMCP):
            # FastMCP instance - use directly
            self._server = server
            self._is_raw_server = False
        elif _is_raw_server(server):
            # Raw mcp.server.Server - wrap with adapter
            from concierge.adapters.raw_server_adapter import RawServerAdapter
            self._server = RawServerAdapter(server)
            self._is_raw_server = True
        else:
            # String name - create new FastMCP instance
            self._server = FastMCP(server, **fastmcp_kwargs)
            self._is_raw_server = False
        self._config = config
        self._widgets: List[Widget] = []
        self._pending_resources: List[types.Resource] = []
        self._assets_dir = Path(assets_dir) if assets_dir else Path.cwd() / "assets"

        provider_cls = _get_provider_class(config.provider_type)
        self._provider = provider_cls()
        self._provider.initialize(config)
        
        self._stages: Dict[str, List[str]] = {}       # stage_name → [tool_names]
        self._transitions: Dict[str, List[str]] = {}  # stage_name → [next_stages]
        self._tool_to_stage: Dict[str, str] = {}      # tool_name → stage_name
        self._default_stage: Optional[str] = None     # First stage (for new sessions)
        self._session_stages: Dict[str, str] = {}     # session_id → current_stage (per-session)
        self._session_state: Dict[str, Dict[str, Any]] = {}  # session_id → {key: value} (per-session state)
        self._all_tools_cache: Dict[str, Any] = {}    # Cache of all registered tools
        self._enforce_completion = True               # Require LLM to reach terminal stage
    
    @property
    def enforce_completion(self) -> bool:
        """If True, instruct LLM that it must continue until reaching a terminal stage."""
        return self._enforce_completion
    
    @enforce_completion.setter
    def enforce_completion(self, value: bool):
        self._enforce_completion = value
    
    def _is_terminal_stage(self, stage: str) -> bool:
        """A stage is terminal if it has no outgoing transitions."""
        return not self._transitions.get(stage, [])
    
    def _get_session_stage(self, session_id: Optional[str]) -> str:
        """Get current stage for a session. Returns default stage for new/unknown sessions."""
        if session_id and session_id in self._session_stages:
            return self._session_stages[session_id]
        return self._default_stage or list(self._stages.keys())[0]
    
    def _set_session_stage(self, session_id: Optional[str], stage: str) -> None:
        """Set current stage for a session."""
        if session_id:
            self._session_stages[session_id] = stage

    # =========== Stage/Workflow Support ===========
    
    @property
    def stages(self) -> Dict[str, List[str]]:
        """Get stages mapping: stage_name → [tool_names]"""
        return self._stages
    
    @stages.setter
    def stages(self, value: Dict[str, List[str]]):
        """Declaratively assign existing tools to stages.
        
        Example:
            app.stages = {
                "browse": ["search_items", "view_details"],
                "checkout": ["add_to_cart", "pay"],
            }
        """
        self._stages = value
        self._tool_to_stage.clear()
        for stage_name, tools in value.items():
            for tool in tools:
                self._tool_to_stage[tool] = stage_name
    
    @property
    def transitions(self) -> Dict[str, List[str]]:
        """Get transitions: stage_name → [allowed_next_stages]"""
        return self._transitions
    
    @transitions.setter
    def transitions(self, value: Dict[str, List[str]]):
        """Define allowed stage transitions.
        
        Example:
            app.transitions = {
                "browse": ["checkout"],
                "checkout": ["payment"],
                "payment": [],
            }
        """
        self._transitions = value
    
    def stage(self, name: str) -> Callable:
        """Decorator to assign a tool to a stage.
        
        Example:
            @app.stage("browse")
            @app.tool()
            def search_items(query: str):
                return {"items": [...]}
        """
        def decorator(fn: Callable) -> Callable:
            tool_name = fn.__name__
            if name not in self._stages:
                self._stages[name] = []
            if tool_name not in self._stages[name]:
                self._stages[name].append(tool_name)
            self._tool_to_stage[tool_name] = name
            return fn
        return decorator
    
    def tool(self, **kwargs) -> Callable:
        """Register a tool. Delegates to underlying FastMCP.
        
        Example:
            @app.tool()
            def my_tool(arg: str) -> dict:
                return {"result": arg}
        """
        return self._server.tool(**kwargs)
    
    def _get_current_session_id(self) -> Optional[str]:
        """Get current session ID from request context."""
        try:
            from mcp.server.lowlevel.server import request_ctx
            ctx = request_ctx.get(None)
            if ctx and ctx.request:
                return ctx.request.headers.get('mcp-session-id')
        except:
            pass
        return None
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a value from session-aware state."""
        session_id = self._get_current_session_id()
        if session_id and session_id in self._session_state:
            return self._session_state[session_id].get(key, default)
        return default
    
    def set_state(self, key: str, value: Any) -> None:
        """Set a value in session-aware state."""
        session_id = self._get_current_session_id()
        if session_id:
            if session_id not in self._session_state:
                self._session_state[session_id] = {}
            self._session_state[session_id][key] = value
    
    def clear_session_state(self, session_id: str) -> None:
        """Clear all state for a session."""
        if session_id in self._session_state:
            del self._session_state[session_id]
    
    def _setup_staged_tools(self) -> None:
        """Override list_tools to only return current stage tools + transition tool."""
        if not self._stages:
            return  # No stages defined, use default flat list
        
        # Set default stage to first stage (for new sessions)
        if self._default_stage is None:
            self._default_stage = list(self._stages.keys())[0]
        
        # Cache all tools by name
        all_tools = self._server._tool_manager.list_tools()
        self._all_tools_cache = {tool.name: tool for tool in all_tools}
        
        instance = self  # Capture for closures
        
        # Create the next_stage tool handler
        async def _handle_next_stage(target_stage: str, ctx: Context = None) -> dict:
            """Transition to the next stage in the workflow."""
            from mcp.server.lowlevel.server import request_ctx
            req_ctx = request_ctx.get()
            session_id = req_ctx.request.headers.get('mcp-session-id')
            
            current = instance._get_session_stage(session_id)
            allowed = instance._transitions.get(current, [])
            
            if target_stage not in allowed:
                return {
                    "error": f"Cannot transition from '{current}' to '{target_stage}'",
                    "allowed_transitions": allowed,
                    "current_stage": current,
                }
            
            instance._set_session_stage(session_id, target_stage)
            
            await req_ctx.session.send_notification(
                types.ServerNotification(types.ToolListChangedNotification()),
                related_request_id=req_ctx.request_id
            )
            
            is_terminal = instance._is_terminal_stage(target_stage)
            
            if instance._enforce_completion:
                if is_terminal:
                    instruction = (
                        "TERMINAL STAGE REACHED. You can call tools in this stage but cannot transition further. "
                        "Execute any remaining tools needed, then provide your final response to the user."
                    )
                else:
                    instruction = (
                        "NON-TERMINAL STAGE. EXECUTION RULES: "
                        "(1) Continue executing tools autonomously. "
                        "(2) Only pause if a tool requires information the user hasn't provided. "
                        "(3) Navigate to the next stage and keep executing until you reach a terminal stage. "
                        "(4) Call terminate_session ONLY if you need to stop or restart."
                    )
            else:
                instruction = None
            
            result = {
                "status": "transitioned",
                "from_stage": current,
                "to_stage": target_stage,
                "message": f"Successfully transitioned from '{current}' to '{target_stage}'.",
            }
            
            if instruction:
                result["instruction"] = instruction
            
            return result
        
        # Register the stage transition tool
        self._server.tool(
            name="proceed_to_next_stage",
            description="Proceed to the next available stage in the workflow, unlocking a new set of tools.",
        )(_handle_next_stage)
        
        # Create the terminate session tool handler
        async def _handle_terminate_session(ctx: Context = None) -> dict:
            """Terminate the current workflow session and reset to initial state."""
            from mcp.server.lowlevel.server import request_ctx
            req_ctx = request_ctx.get()
            session_id = req_ctx.request.headers.get('mcp-session-id')
            
            current = instance._get_session_stage(session_id)
            initial = instance._default_stage
            
            # Reset session stage to initial
            if session_id and session_id in instance._session_stages:
                del instance._session_stages[session_id]
            
            # Clear session state (cart, orders, etc.)
            if session_id:
                instance.clear_session_state(session_id)
            
            await req_ctx.session.send_notification(
                types.ServerNotification(types.ToolListChangedNotification()),
                related_request_id=req_ctx.request_id
            )
            
            return {
                "status": "terminated",
                "previous_stage": current,
                "message": f"Session terminated. Workflow and state reset from '{current}' to initial stage '{initial}'. You can now start a fresh workflow or switch to a different task.",
            }
        
        # Register the terminate session tool
        self._server.tool(
            name="terminate_session",
            description="Terminate the current workflow session and reset to the beginning. Call this when: (1) the user wants to start over, (2) the user changes their mind and wants to do something different, (3) the user explicitly asks to stop/cancel/abort, or (4) you have completed the workflow and the user indicates they are done.",
        )(_handle_terminate_session)
        
        original_list_tools = self._server.list_tools
        
        async def filtered_list_tools():
            """Return only tools from the current stage."""
            from mcp.server.lowlevel.server import request_ctx
            ctx = request_ctx.get(None)
            session_id = None
            if ctx and ctx.request:  
                session_id = ctx.request.headers.get('mcp-session-id')
            
            current_stage = instance._get_session_stage(session_id)
            current_stage_tool_names = instance._stages.get(current_stage, [])
            next_stages = instance._transitions.get(current_stage, [])
            
            all_tools = await original_list_tools()
            
            visible_tools = []
            for tool in all_tools:
                if tool.name in current_stage_tool_names:
                    tool_copy = tool.model_copy()
                    tool_copy.description = f"[{current_stage}] {tool.description or ''}"
                    visible_tools.append(tool_copy)
            
            # Add stage transition tool
            if next_stages:
                from mcp.types import Tool as MCPTool
                stage_list = ", ".join(f"'{s}'" for s in next_stages)
                visible_tools.append(MCPTool(
                    name="proceed_to_next_stage",
                    description=(
                        f"Proceed to the next available stage in the workflow. "
                        f"This will unlock a new set of tools and allow you to continue. "
                        f"Currently in stage '{current_stage}'. "
                        f"Available stages to proceed to: {stage_list}."
                    ),
                    inputSchema={
                        "type": "object",
                        "title": "StageTransitionRequest",
                        "description": "Request to transition to a different stage in the workflow.",
                        "properties": {
                            "target_stage": {
                                "type": "string",
                                "title": "Target Stage",
                                "description": (
                                    f"The name of the stage to transition to. "
                                    f"Must be one of the available stages: {stage_list}."
                                ),
                                "enum": next_stages,
                            }
                        },
                        "required": ["target_stage"],
                        "additionalProperties": False,
                    },
                ))
            
            # Add terminate_session tool (always visible)
            from mcp.types import Tool as MCPTool
            visible_tools.append(MCPTool(
                name="terminate_session",
                description=(
                    "Terminate the current workflow session and reset to the beginning. "
                    "Call this when: (1) the user wants to start over, (2) the user changes their mind and wants to do something different, "
                    "(3) the user explicitly asks to stop/cancel/abort, or (4) you have completed the workflow and the user indicates they are done."
                ),
                inputSchema={
                    "type": "object",
                    "title": "TerminateSessionRequest",
                    "description": "Request to terminate the current workflow session.",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False,
                },
            ))
            
            return visible_tools
        
        self._server.list_tools = filtered_list_tools
        self._server._mcp_server.list_tools()(filtered_list_tools)
    
    # =========== End Stage Support ===========

    def _get_widget_meta(self, w: Widget) -> dict:
        return {
            "openai/outputTemplate": w.uri,
            "openai/widgetAccessible": w.widget_accessible,
            "openai/toolInvocation/invoking": w.invoking,
            "openai/toolInvocation/invoked": w.invoked,
        }

    def _setup_resource_handler(self) -> None:
        original_list_resources = self._server.list_resources
        widget_resources = self._pending_resources

        async def _list_all_resources() -> List[types.Resource]:
            fastmcp_resources = await original_list_resources()
            return fastmcp_resources + widget_resources

        self._server._mcp_server.list_resources()(_list_all_resources)

    def _get_widget_html(self, widget: Widget) -> str:
        """Get HTML content for a widget based on its mode."""
        mode = widget.mode
        
        if mode == WidgetMode.HTML:
            return widget.html
        
        if mode == WidgetMode.URL:
            return IFRAME_TEMPLATE.format(url=widget.url)
        
        if mode == WidgetMode.ENTRYPOINT:
            dist_path = self._assets_dir / "dist" / widget.dist_file
            if not dist_path.exists():
                raise FileNotFoundError(
                    f"Widget {widget.name}: dist/{widget.dist_file} not found. "
                    f"Run 'npm run build' in {self._assets_dir}"
                )
            return dist_path.read_text()
        
        if mode == WidgetMode.DYNAMIC:
            if not hasattr(widget, '_last_args') or widget._last_args is None:
                raise ValueError(f"Widget {widget.name}: call the tool first")
            return widget.html_fn(widget._last_args)
        
        raise ValueError(f"Unknown widget mode: {mode}")

    def _setup_read_resource_handler(self) -> None:
        widgets_by_uri = {w.uri: w for w in self._widgets}
        get_html = self._get_widget_html

        original_handler = self._server._mcp_server.request_handlers.get(
            types.ReadResourceRequest
        )

        async def _read_resource_with_meta(
            req: types.ReadResourceRequest,
        ) -> types.ServerResult:
            uri_str = str(req.params.uri)
            widget = widgets_by_uri.get(uri_str)

            if widget:
                text = get_html(widget)
                contents = [
                    types.TextResourceContents(
                        uri=widget.uri,
                        mimeType=widget.mime_type,
                        text=text,
                        _meta=self._get_widget_meta(widget),
                    )
                ]
                return types.ServerResult(types.ReadResourceResult(contents=contents))

            if original_handler:
                return await original_handler(req)

            raise ValueError(f"Unknown resource: {uri_str}")

        self._server._mcp_server.request_handlers[
            types.ReadResourceRequest
        ] = _read_resource_with_meta

    def _run_widget_builds(self):
        """Auto-run npm build if any widget uses entrypoint mode."""
        needs_build = any(w.mode == WidgetMode.ENTRYPOINT for w in self._widgets)
        if not needs_build:
            return
        
        package_json = self._assets_dir / "package.json"
        if not package_json.exists():
            raise FileNotFoundError(
                f"{self._assets_dir}/package.json not found. "
                f"Widgets using entrypoint mode require a build system."
            )
        
        print("Installing web dependencies...", flush=True)
        result = subprocess.run(
            ["npm", "install"],
            cwd=str(self._assets_dir),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"npm install failed:\n{result.stderr}")
        
        print("Building widgets...", flush=True)
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=str(self._assets_dir),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Build failed:\n{result.stdout}\n{result.stderr}")
        print("Build complete", flush=True)

    def _finalize(self):
        """Setup all handlers. Called before run() or streamable_http_app()."""
        if getattr(self, "_finalized", False):
            return
        self._finalized = True

        self._run_widget_builds()

        tools = self._server._tool_manager.list_tools()
        self._provider.index_tools(tools)

        served_tools = self._provider.serve_tools()
        self._server._tool_manager._tools = {t.name: t for t in served_tools}

        self._setup_resource_handler()
        self._setup_read_resource_handler()
        self._setup_staged_tools()  # Organize tools by stage if stages defined
        self._setup_metrics()

    def _setup_metrics(self):
        if not METRICS_ENABLED:
            return
        handlers = self._server._mcp_server.request_handlers

        if types.CallToolRequest in handlers:
            original = handlers[types.CallToolRequest]
            async def wrapped_call(req: types.CallToolRequest) -> types.ServerResult:
                metrics.ensure_started()
                start = time.perf_counter()
                is_error, error_msg = False, None
                try:
                    return await original(req)
                except Exception as e:
                    is_error, error_msg = True, str(e)
                    raise
                finally:
                    metrics.track("mcp:tools/call", resource_name=req.params.name,
                                  duration_ms=int((time.perf_counter() - start) * 1000),
                                  is_error=is_error, error_message=error_msg)
            handlers[types.CallToolRequest] = wrapped_call

        if types.ReadResourceRequest in handlers:
            original_read = handlers[types.ReadResourceRequest]
            async def wrapped_read(req: types.ReadResourceRequest) -> types.ServerResult:
                metrics.ensure_started()
                start = time.perf_counter()
                is_error, error_msg = False, None
                try:
                    return await original_read(req)
                except Exception as e:
                    is_error, error_msg = True, str(e)
                    raise
                finally:
                    metrics.track("mcp:resources/read", resource_name=str(req.params.uri),
                                  duration_ms=int((time.perf_counter() - start) * 1000),
                                  is_error=is_error, error_message=error_msg)
            handlers[types.ReadResourceRequest] = wrapped_read

    def run(self, *args, **kwargs):
        self._finalize()
        metrics.start()
        return self._server.run(*args, **kwargs)

    def streamable_http_app(self):
        self._finalize()
        metrics.start()
        app = self._server.streamable_http_app()
        
        # Add session tracking middleware using Starlette's middleware system
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.requests import Request
        
        concierge_instance = self
        
        class SessionTrackingMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request: Request, call_next):
                # Track session for task-based lookups (fallback method)
                session_id = request.headers.get('mcp-session-id')
                task = asyncio.current_task()
                task_id = id(task) if task else None
                if task_id and session_id:
                    _task_session_map[task_id] = session_id
                return await call_next(request)
        
        app.add_middleware(SessionTrackingMiddleware)
        return app

    def widget(
        self,
        uri: str,
        # Mode 1: Inline HTML
        html: Optional[str] = None,
        # Mode 2: External URL  
        url: Optional[str] = None,
        # Mode 3: Entrypoint (filename in entrypoints/)
        entrypoint: Optional[str] = None,
        # Mode 4: Dynamic function (takes args dict, returns HTML string)
        html_fn: Optional[Callable[[dict], str]] = None,
        # Metadata
        name: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        invoking: str = "Loading...",
        invoked: str = "Done",
        annotations: Optional[dict] = None,
    ) -> Callable:

        def decorator(fn: Callable) -> Callable:
            w = Widget(
                uri=uri,
                html=html,
                url=url,
                entrypoint=entrypoint,
                html_fn=html_fn,
                name=name or fn.__name__,
                title=title,
                description=description or fn.__doc__,
                invoking=invoking,
                invoked=invoked,
                annotations=annotations,
            )
            self._widgets.append(w)
            self._pending_resources.append(
                types.Resource(
                    uri=w.uri,
                    name=w.name,
                    title=w.title,
                    description=w.description,
                    mimeType=w.mime_type,
                    _meta=self._get_widget_meta(w),
                )
            )

            @wraps(fn)
            async def wrapped(*args, **kwargs) -> types.CallToolResult:
                result = await fn(*args, **kwargs)
                
                if w.html_fn:
                    w._last_args = result
                
                return types.CallToolResult(
                    content=[types.TextContent(type="text", text=w.invoked)],
                    structuredContent=result,
                    _meta={
                        "openai/toolInvocation/invoking": w.invoking,
                        "openai/toolInvocation/invoked": w.invoked,
                    },
                )

            self._server.tool(
                name=w.name,
                title=w.title,
                description=w.description,
                annotations=w.annotations,
                meta={
                    "openai/outputTemplate": w.uri,
                    "openai/widgetAccessible": w.widget_accessible,
                    "openai/toolInvocation/invoking": w.invoking,
                    "openai/toolInvocation/invoked": w.invoked,
                },
            )(wrapped)

            return fn

        return decorator

    def __getattr__(self, name):
        return getattr(self._server, name)


# Backwards compatibility alias
OpenMCP = Concierge
