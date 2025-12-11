from typing import Optional, Set
from fastmcp import FastMCP, Context
import tempfile
import json
from pathlib import Path
from aristotlelib.project import Project, ProjectStatus, ProjectInputType

# Global state for monitoring
monitored_projects: Set[str] = set()

# Initialize FastMCP
mcp = FastMCP("aristotle-mcp")

@mcp.tool()
async def prove_lean_file(
    file_path: str,
    ctx: Context | None = None,
) -> str:
    """
    Submits a local Lean file to Aristotle to fill in 'sorry' placeholders.
    Returns the Project ID immediately. The server will poll in the background and notify when done.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if ctx:
        await ctx.info(f"Submitting {file_path} to Aristotle...")
    
    project_id = await Project.prove_from_file( # type: ignore
        input_file_path=path,
        project_input_type=ProjectInputType.FORMAL_LEAN,
        wait_for_completion=False
    )
    
    monitored_projects.add(project_id)
    return f"Project started with ID: {project_id}. You will be notified when it completes."

@mcp.tool()
async def prove_informal(
    file_path: str,
    formal_context_path: Optional[str] = None,
    ctx: Context | None = None,
) -> str:
    """
    Submits a file containing natural language mathematics (Text, Markdown, LaTeX) to be formalised and proved.
    Returns the Project ID immediately.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if ctx:
        await ctx.info(f"Submitting informal file {file_path} to Aristotle...")

    project_id = await Project.prove_from_file( # type: ignore
        input_file_path=path,
        project_input_type=ProjectInputType.INFORMAL,
        formal_input_context=formal_context_path,
        wait_for_completion=False
    )

    monitored_projects.add(project_id)
    return f"Project started with ID: {project_id}. You will be notified when it completes."

@mcp.tool()
async def get_project_status(
    project_id: str,
    save_solution_to: Optional[str] = None,
) -> str:
    """
    Checks the status of a specific Aristotle project.
    Returns full project data including solution if available.
    """
    project = await Project.from_id(project_id)
    
    data = {
        "project_id": project.project_id,
        "status": project.status.value,
        "created_at": project.created_at.isoformat(),
        "last_updated_at": project.last_updated_at.isoformat(),
        "file_name": project.file_name,
        "description": project.description,
    }
    
    if project.status == ProjectStatus.COMPLETE:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "solution.lean"
                await project.get_solution(output_path=output_path)
                if output_path.exists():
                    solution_content = output_path.read_text()
                    data["solution"] = solution_content
                    
                    if save_solution_to:
                        save_path = Path(save_solution_to)
                        save_path.write_text(solution_content)
                        data["saved_to"] = str(save_path.absolute())
        except Exception as e:
            data["solution_error"] = str(e)
            
    return json.dumps(data, indent=2)

@mcp.tool()
async def list_recent_projects(
    limit: int = 10,
    save_to: Optional[str] = None,
) -> str:
    """
    Lists the most recent projects submitted to Aristotle.
    """
    projects, _ = await Project.list_projects(limit=limit)
    
    lines = []
    for p in projects:
        lines.append(f"Project: {p.project_id}, Status: {p.status.value}, Created: {p.created_at}")
    
    result = "\n".join(lines)
    
    if save_to:
        Path(save_to).write_text(result)
        return f"Project list saved to {save_to}"
    
    return result

@mcp.tool()
async def prove_lean_code(
    lean_code: str,
    ctx: Context | None = None,
) -> str:
    """
    Submits Lean code directly to Aristotle to fill in 'sorry' placeholders.
    Returns the Project ID immediately.
    """
    if ctx:
        await ctx.info("Submitting Lean code to Aristotle...")
    
    project_id = await Project.prove_from_file( # type: ignore
        input_content=lean_code,
        project_input_type=ProjectInputType.FORMAL_LEAN,
        wait_for_completion=False
    )
    
    monitored_projects.add(project_id)
    return f"Project started with ID: {project_id}."

@mcp.tool()
async def prove_informal_text(
    text: str,
    formal_context_path: Optional[str] = None,
    ctx: Context | None = None,
) -> str:
    """
    Submits natural language mathematics directly to be formalized and proved.
    Returns the Project ID immediately.
    """
    if ctx:
        await ctx.info("Submitting informal text to Aristotle...")
    
    project_id = await Project.prove_from_file( # type: ignore
        input_content=text,
        project_input_type=ProjectInputType.INFORMAL,
        formal_input_context=formal_context_path,
        wait_for_completion=False
    )
    
    monitored_projects.add(project_id)
    return f"Project started with ID: {project_id}."

@mcp.resource("aristotle://projects")
async def list_projects_resource() -> str:
    """A live list of the user's recent projects."""
    projects, _ = await Project.list_projects(limit=20)
    # Return as JSON string
    data = [
        {
            "project_id": p.project_id,
            "status": p.status.value,
            "created_at": p.created_at.isoformat(),
            "file_name": p.file_name,
            "description": p.description
        }
        for p in projects
    ]
    return json.dumps(data, indent=2)

@mcp.resource("aristotle://projects/{project_id}")
async def get_project_resource(project_id: str) -> str:
    """The status and result of a particular project."""
    project = await Project.from_id(project_id)
    
    data = {
        "project_id": project.project_id,
        "status": project.status.value,
        "created_at": project.created_at.isoformat(),
        "last_updated_at": project.last_updated_at.isoformat(),
        "file_name": project.file_name,
        "description": project.description,
    }
    
    if project.status == ProjectStatus.COMPLETE:
        # Include solution content
        try:
             with tempfile.TemporaryDirectory() as temp_dir:
                output_path = Path(temp_dir) / "solution.lean"
                await project.get_solution(output_path=output_path)
                if output_path.exists():
                    data["solution"] = output_path.read_text()
        except Exception as e:
            data["solution_error"] = str(e)
            
    return json.dumps(data, indent=2)

if __name__ == "__main__":
    mcp.run()
