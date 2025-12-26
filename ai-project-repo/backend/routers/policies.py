import json
import os
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/policies",
    tags=["Policies"]
)

# --- Configuration ---
POLICIES_DIR = "storage/policies"
TEMPLATES_DIR = "storage/templates"

# Ensure directories exist
os.makedirs(POLICIES_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# --- Pydantic Models ---
class PolicyBase(BaseModel):
    name: str
    content: str
    type: str  # 'policies' or 'report_templates'

class PolicyCreate(PolicyBase):
    pass

class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None

class Policy(PolicyBase):
    id: str
    created_at: str
    updated_at: str

class PolicyResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Policy] = None

class PoliciesListResponse(BaseModel):
    success: bool
    message: str
    data: List[Policy]

# --- Service Class ---
class PoliciesService:
    def __init__(self):
        pass

    def _get_file_path(self, policy_type: str, policy_id: str) -> str:
        """Get the file path for a policy or template."""
        if policy_type == "policies":
            return os.path.join(POLICIES_DIR, f"{policy_id}.json")
        elif policy_type == "report_templates":
            return os.path.join(TEMPLATES_DIR, f"{policy_id}.json")
        else:
            raise HTTPException(status_code=400, detail="Invalid policy type")

    def _get_directory(self, policy_type: str) -> str:
        """Get the directory for a policy type."""
        if policy_type == "policies":
            return POLICIES_DIR
        elif policy_type == "report_templates":
            return TEMPLATES_DIR
        else:
            raise HTTPException(status_code=400, detail="Invalid policy type")

    def _generate_id(self, name: str) -> str:
        """Generate a unique ID based on name and timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        clean_name = clean_name.replace(' ', '_').lower()
        return f"{clean_name}_{timestamp}"

    def create_policy(self, policy_data: PolicyCreate) -> Policy:
        """Create a new policy or template."""
        try:
            policy_id = self._generate_id(policy_data.name)
            now = datetime.now().isoformat()
            
            policy = Policy(
                id=policy_id,
                name=policy_data.name,
                content=policy_data.content,
                type=policy_data.type,
                created_at=now,
                updated_at=now
            )
            
            file_path = self._get_file_path(policy_data.type, policy_id)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(policy.dict(), f, indent=2, ensure_ascii=False)
            
            return policy
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating policy: {str(e)}")

    def get_policies(self, policy_type: str) -> List[Policy]:
        """Get all policies or templates of a specific type."""
        try:
            directory = self._get_directory(policy_type)
            policies = []
            
            for filename in os.listdir(directory):
                if filename.endswith('.json'):
                    file_path = os.path.join(directory, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        policy_data = json.load(f)
                        policies.append(Policy(**policy_data))
            
            # Sort by creation date (newest first)
            policies.sort(key=lambda x: x.created_at, reverse=True)
            return policies
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving policies: {str(e)}")

    def get_policy(self, policy_type: str, policy_id: str) -> Policy:
        """Get a specific policy or template by ID."""
        try:
            file_path = self._get_file_path(policy_type, policy_id)
            
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Policy not found")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                policy_data = json.load(f)
                return Policy(**policy_data)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving policy: {str(e)}")

    def update_policy(self, policy_type: str, policy_id: str, update_data: PolicyUpdate) -> Policy:
        """Update an existing policy or template."""
        try:
            # Get existing policy
            existing_policy = self.get_policy(policy_type, policy_id)
            
            # Update fields if provided
            updated_data = existing_policy.dict()
            if update_data.name is not None:
                updated_data['name'] = update_data.name
            if update_data.content is not None:
                updated_data['content'] = update_data.content
            
            updated_data['updated_at'] = datetime.now().isoformat()
            
            policy = Policy(**updated_data)
            
            # Save updated policy
            file_path = self._get_file_path(policy_type, policy_id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(policy.dict(), f, indent=2, ensure_ascii=False)
            
            return policy
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating policy: {str(e)}")

    def delete_policy(self, policy_type: str, policy_id: str) -> bool:
        """Delete a policy or template."""
        try:
            file_path = self._get_file_path(policy_type, policy_id)
            
            if not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="Policy not found")
            
            os.remove(file_path)
            return True
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting policy: {str(e)}")

# Initialize service
policies_service = PoliciesService()

# --- API Endpoints ---

@router.post("/", response_model=PolicyResponse)
def create_policy(policy_data: PolicyCreate):
    """Create a new policy or report template."""
    try:
        policy = policies_service.create_policy(policy_data)
        return PolicyResponse(
            success=True,
            message="Policy created successfully",
            data=policy
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{policy_type}", response_model=PoliciesListResponse)
def get_policies(policy_type: str):
    """Get all policies or templates of a specific type."""
    if policy_type not in ["policies", "report_templates"]:
        raise HTTPException(status_code=400, detail="Invalid policy type")
    
    try:
        policies = policies_service.get_policies(policy_type)
        return PoliciesListResponse(
            success=True,
            message=f"Retrieved {len(policies)} {policy_type}",
            data=policies
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{policy_type}/{policy_id}", response_model=PolicyResponse)
def get_policy(policy_type: str, policy_id: str):
    """Get a specific policy or template by ID."""
    if policy_type not in ["policies", "report_templates"]:
        raise HTTPException(status_code=400, detail="Invalid policy type")
    
    try:
        policy = policies_service.get_policy(policy_type, policy_id)
        return PolicyResponse(
            success=True,
            message="Policy retrieved successfully",
            data=policy
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{policy_type}/{policy_id}", response_model=PolicyResponse)
def update_policy(policy_type: str, policy_id: str, update_data: PolicyUpdate):
    """Update an existing policy or template."""
    if policy_type not in ["policies", "report_templates"]:
        raise HTTPException(status_code=400, detail="Invalid policy type")
    
    try:
        policy = policies_service.update_policy(policy_type, policy_id, update_data)
        return PolicyResponse(
            success=True,
            message="Policy updated successfully",
            data=policy
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{policy_type}/{policy_id}")
def delete_policy(policy_type: str, policy_id: str):
    """Delete a policy or template."""
    if policy_type not in ["policies", "report_templates"]:
        raise HTTPException(status_code=400, detail="Invalid policy type")
    
    try:
        policies_service.delete_policy(policy_type, policy_id)
        return {
            "success": True,
            "message": "Policy deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{policy_type}/{policy_id}/export")
def export_policy(policy_type: str, policy_id: str):
    """Export a policy or template as JSON."""
    if policy_type not in ["policies", "report_templates"]:
        raise HTTPException(status_code=400, detail="Invalid policy type")
    
    try:
        policy = policies_service.get_policy(policy_type, policy_id)
        from fastapi.responses import JSONResponse
        
        return JSONResponse(
            content=policy.dict(),
            headers={
                "Content-Disposition": f"attachment; filename={policy.name}_{policy_id}.json"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
