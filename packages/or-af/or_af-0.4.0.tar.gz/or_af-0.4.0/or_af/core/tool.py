"""
OR-AF Core Module - Tool implementation
"""

import inspect
import time
from typing import Callable, Dict, Any, Optional
from pydantic import BaseModel, Field

from ..models.tool_models import ToolSchema, ToolResult
from ..exceptions import ToolExecutionError
from ..utils.logger import default_logger


class Tool(BaseModel):
    """Represents a tool that can be used by agents via MCP servers."""
    
    name: str = Field(..., description="Tool name")
    func: Callable = Field(..., description="Tool function")
    description: str = Field(..., description="Tool description")
    
    class Config:
        arbitrary_types_allowed = True
        extra = "allow"
    
    def __init__(self, name: str, func: Callable, description: Optional[str] = None, **kwargs):
        """Initialize tool."""
        desc = description or func.__doc__ or "No description provided"
        super().__init__(name=name, func=func, description=desc, **kwargs)
        object.__setattr__(self, 'logger', default_logger)
    
    def _extract_parameters(self) -> Dict[str, Any]:
        """Extract function parameters and create OpenAI function schema."""
        sig = inspect.signature(self.func)
        properties = {}
        required = []
        
        logger = object.__getattribute__(self, 'logger')
        logger.debug(f"Extracting parameters for tool: {self.name}")
        
        for param_name, param in sig.parameters.items():
            param_type = "string"
            param_desc = f"Parameter {param_name}"
            
            if param.annotation != inspect.Parameter.empty:
                annotation = param.annotation
                
                if hasattr(annotation, '__origin__'):
                    if annotation.__origin__ is type(None):
                        continue
                    annotation = annotation.__args__[0] if annotation.__args__ else annotation
                
                if annotation == int:
                    param_type = "integer"
                elif annotation == float:
                    param_type = "number"
                elif annotation == bool:
                    param_type = "boolean"
                elif annotation == list:
                    param_type = "array"
                elif annotation == dict:
                    param_type = "object"
                elif annotation == str:
                    param_type = "string"
            
            properties[param_name] = {
                "type": param_type,
                "description": param_desc
            }
            
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def get_schema(self) -> ToolSchema:
        """Get tool schema."""
        parameters = self._extract_parameters()
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=parameters
        )
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert tool to OpenAI function calling format."""
        schema = self.get_schema()
        return schema.to_openai_format()
    
    def execute(self, tool_call_id: str, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        logger = object.__getattribute__(self, 'logger')
        logger.info(f"Executing tool: {self.name} with args: {kwargs}")
        start_time = time.time()
        
        try:
            result = self.func(**kwargs)
            execution_time = time.time() - start_time
            
            logger.info(f"Tool {self.name} completed successfully in {execution_time:.3f}s")
            
            return ToolResult(
                tool_call_id=tool_call_id,
                tool_name=self.name,
                result=result,
                execution_time=execution_time
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Error in tool {self.name}: {str(e)}"
            logger = object.__getattribute__(self, 'logger')
            logger.error(error_msg, exc_info=True)
            
            return ToolResult(
                tool_call_id=tool_call_id,
                tool_name=self.name,
                result=None,
                error=error_msg,
                execution_time=execution_time
            )
    
    def __str__(self) -> str:
        return f"Tool(name={self.name}, description={self.description})"
    
    def __repr__(self) -> str:
        return self.__str__()
