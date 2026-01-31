"""CodeSearch - Semantic search for code by meaning/behavior."""

import asyncio
from typing import override

from kosong.tooling import CallableTool2, ToolReturnValue, ToolOk, ToolError
from pydantic import BaseModel, Field

from axe_cli.soul.agent import Runtime
from axe_cli.tools.utils import ToolResultBuilder


class CodeSearchParams(BaseModel):
    """Parameters for CodeSearch tool."""
    
    query: str = Field(
        description="Natural language search query describing the code behavior or functionality you're looking for."
    )
    path: str = Field(
        description="Project path to search in. Defaults to current directory.",
        default="."
    )


class CodeSearch(CallableTool2[CodeSearchParams]):
    """
    Semantic search for code by meaning/behavior using axe-dig.
    
    Runs: `chop semantic search "<query>" --path <path>`
    
    Unlike grep which matches text, this searches by what code DOES.
    Example: "validate JWT tokens" finds verify_access_token() even without that exact text.
    """
    
    name: str = "CodeSearch"
    params: type[CodeSearchParams] = CodeSearchParams
    
    def __init__(self, runtime: Runtime):
        description = """Semantic search for code by meaning/behavior.

Runs: `chop semantic search "<query>" --path <path>`

Search by what code DOES, not just what it says. Uses vector embeddings 
to find functions by their purpose, even without exact text matches.

**Examples:**
- "validate JWT tokens and check expiration" → finds verify_access_token()
- "database connection pooling" → finds connection management code  
- "recursion cycle" → finds mutually recursive functions
- "error handling for API requests" → finds exception handlers

**Result format:** Returns function names with relevance scores (0-1).

**Note:** The codebase is automatically indexed on startup, so semantic search should work immediately.

Example:
```json
{"query": "parse and validate user input", "path": "."}
```
"""
        super().__init__(description=description)
        self._runtime = runtime
        self._work_dir = runtime.builtin_args.AXE_WORK_DIR
    
    @override
    async def __call__(self, params: CodeSearchParams) -> ToolReturnValue:
        builder = ToolResultBuilder()
        
        if not params.query.strip():
            return ToolError(
                message="Search query cannot be empty.",
                brief="Empty query"
            )
        
        path = params.path
        if path == ".":
            path = str(self._work_dir)
        
        builder.write(f"🔍 Searching: \"{params.query}\"\n\n")
        
        try:
            # Escape single quotes in query
            escaped_query = params.query.replace("'", "'\"'\"'")
            cmd = f"chop semantic search '{escaped_query}' --path {path}"
            
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._work_dir)
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = stdout.decode().strip()
                if output:
                    builder.write(output)
                    builder.write("\n")
                    return builder.ok(brief="Search complete")
                else:
                    return ToolOk(
                        message="No results found. Try:\n1. Using different search terms\n2. Checking if the semantic index exists\n3. Running 'chop semantic index .' in terminal to rebuild",
                        brief="No results"
                    )
            else:
                error_msg = stderr.decode().strip() or stdout.decode().strip()
                if "index" in error_msg.lower() or "not found" in error_msg.lower():
                    return ToolError(
                        message=f"Semantic index not found. The codebase may not be initialized.\n\nError: {error_msg}",
                        brief="Index not found"
                    )
                return ToolError(
                    message=f"Search failed: {error_msg}",
                    brief="Search failed"
                )
                
        except FileNotFoundError:
            return ToolError(
                message="chop command not found. Make sure axe-dig is installed: pip install axe-dig",
                brief="axe-dig not installed"
            )
        except Exception as e:
            return ToolError(
                message=f"Search failed: {str(e)}",
                brief="Error"
            )
