from fastapi import APIRouter, HTTPException
from typing import Any, Dict

class BaseController:
    """
    All user-defined controllers should inherit from this.
    It provides helper methods for standard JSON responses.
    """
    
    def __init__(self):
        self.router = APIRouter()

    def success(self, data: Any, message: str = "Success") -> Dict[str, Any]:
        """
        Standard success response format.
        {
            "status": "success",
            "message": "Operation completed",
            "data": { ... }
        }
        """
        return {
            "status": "success",
            "message": message,
            "data": data
        }

    def error(self, message: str, code: int = 400):
        """
        Raises a standard HTTP exception.
        """
        raise HTTPException(status_code=code, detail=message)