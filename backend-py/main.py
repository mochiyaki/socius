from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from datetime import datetime
import uuid
import logging

from models import (
    Agent, AgentCreate, AgentUpdate, AgentStatus,
    ChatRequest, ChatResponse, ContentQuery
)
from config import settings
from services.redis_service import redis_service
from services.sanity_service import sanity_service
from services.agent_service import agent_service
from services.mcp_server import mcp_server

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MCP Agent API",
    description="FastAPI backend with Redis, LangChain, Claude Sonnet 4.5, and Sanity CMS",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_status = redis_service.ping()
    return {
        "status": "healthy" if redis_status else "degraded",
        "redis": "connected" if redis_status else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MCP Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Agent Endpoints
@app.post("/agents", response_model=Agent, status_code=status.HTTP_201_CREATED)
async def create_agent(agent_data: AgentCreate):
    """Create a new agent"""
    try:
        agent_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        agent = {
            "id": agent_id,
            "name": agent_data.name,
            "description": agent_data.description,
            "system_prompt": agent_data.system_prompt,
            "temperature": agent_data.temperature,
            "max_tokens": agent_data.max_tokens,
            "status": AgentStatus.ACTIVE.value,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "metadata": agent_data.metadata or {}
        }
        
        success = redis_service.save_agent(agent_id, agent)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create agent"
            )
        
        logger.info(f"Created agent: {agent_id}")
        return agent
    except Exception as e:
        logger.error(f"Error creating agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/agents", response_model=list[Agent])
async def list_agents():
    """List all agents"""
    try:
        agents = redis_service.get_all_agents()
        return agents
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/agents/{agent_id}", response_model=Agent)
async def get_agent_by_id(agent_id: str):
    """Retrieve a specific agent by ID"""
    try:
        agent = redis_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        return agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.put("/agents/{agent_id}", response_model=Agent)
async def update_agent(agent_id: str, updates: AgentUpdate):
    """Update an agent"""
    try:
        agent = redis_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        update_data = updates.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        success = redis_service.update_agent(agent_id, update_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update agent"
            )
        
        updated_agent = redis_service.get_agent(agent_id)
        logger.info(f"Updated agent: {agent_id}")
        return updated_agent
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.delete("/agents/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str):
    """Delete an agent"""
    try:
        agent = redis_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {agent_id} not found"
            )
        
        success = redis_service.delete_agent(agent_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete agent"
            )
        
        logger.info(f"Deleted agent: {agent_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
