"""
Agent API Routes - REST endpoints for AI agent capabilities
Exposes the KraftdAI Agent via FastAPI endpoints for document analysis, chat, and status queries.
"""

from fastapi import APIRouter, HTTPException, status, Header, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import json
import uuid

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])

# Global agent instance (lazy-loaded)
_agent_instance = None

# ===== Pydantic Models for Request/Response =====

class AgentAnalyzeRequest(BaseModel):
    """Request model for document analysis"""
    document_id: str = Field(..., description="ID of the document to analyze")
    document_type: Optional[str] = Field(None, description="Type of document (e.g., 'invoice', 'po', 'quotation')")
    analysis_type: Optional[str] = Field("comprehensive", description="Type of analysis: 'comprehensive', 'quick', 'extract', 'validate'")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for analysis")
    
    class Config:
        schema_extra = {
            "example": {
                "document_id": "doc_12345",
                "document_type": "invoice",
                "analysis_type": "comprehensive",
                "metadata": {"vendor_id": "vendor_001"}
            }
        }


class AgentChatRequest(BaseModel):
    """Request model for agent chat"""
    message: str = Field(..., description="User message for the agent")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context. If not provided, a new one is created.")
    include_history: Optional[bool] = Field(True, description="Whether to include conversation history")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Analyze this invoice for risks and compare with previous invoices",
                "conversation_id": "conv_abc123",
                "include_history": True
            }
        }


class AgentAnalyzeResponse(BaseModel):
    """Response model for document analysis"""
    status: str = Field(..., description="Status of the analysis: 'success', 'error', 'partial'")
    document_id: str = Field(..., description="ID of the analyzed document")
    analysis_result: Dict[str, Any] = Field(..., description="Analysis results including extracted data, risks, recommendations")
    confidence_score: Optional[float] = Field(None, description="Confidence score of the analysis (0.0-1.0)")
    processing_time_ms: float = Field(..., description="Time taken to process in milliseconds")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the analysis")
    error_message: Optional[str] = Field(None, description="Error message if status is 'error'")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "document_id": "doc_12345",
                "analysis_result": {
                    "extracted_fields": {
                        "vendor": "ACME Corp",
                        "total_amount": 1500.00,
                        "due_date": "2025-02-15"
                    },
                    "risks": [
                        {"type": "unusual_amount", "severity": "medium", "description": "Amount is 30% higher than average"}
                    ],
                    "recommendations": ["Compare with vendor baseline", "Check against PO"]
                },
                "confidence_score": 0.92,
                "processing_time_ms": 2345,
                "timestamp": "2025-01-18T14:30:00Z"
            }
        }


class AgentChatResponse(BaseModel):
    """Response model for agent chat"""
    status: str = Field(..., description="Status of the chat: 'success', 'error'")
    conversation_id: str = Field(..., description="Conversation ID for this interaction")
    message: str = Field(..., description="User's original message")
    response: str = Field(..., description="Agent's response")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Any tool calls made by the agent")
    processing_time_ms: float = Field(..., description="Time taken to process in milliseconds")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the interaction")
    error_message: Optional[str] = Field(None, description="Error message if status is 'error'")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "conversation_id": "conv_abc123",
                "message": "What risks do you see in this invoice?",
                "response": "Based on the analysis, I found 2 medium-severity risks...",
                "tool_calls": [
                    {"function": "extract_intelligence", "params": {"document_id": "doc_12345"}}
                ],
                "processing_time_ms": 3456,
                "timestamp": "2025-01-18T14:35:00Z"
            }
        }


class AgentStatusResponse(BaseModel):
    """Response model for agent status"""
    status: str = Field(..., description="Agent status: 'ready', 'initializing', 'error'")
    version: str = Field(..., description="Agent version")
    capabilities: List[str] = Field(..., description="List of available capabilities")
    model: str = Field(..., description="LLM model being used")
    available_tools: List[str] = Field(..., description="List of available tools")
    uptime_seconds: float = Field(..., description="Agent uptime in seconds")
    message: Optional[str] = Field(None, description="Status message")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "ready",
                "version": "1.0.0",
                "capabilities": [
                    "document_analysis",
                    "conversation",
                    "document_intelligence",
                    "risk_detection",
                    "document_learning"
                ],
                "model": "gpt-4",
                "available_tools": [
                    "upload_document",
                    "extract_intelligence",
                    "validate_document",
                    "compare_quotations",
                    "detect_risks",
                    "create_po"
                ],
                "uptime_seconds": 3600.5,
                "message": "Agent initialized and ready"
            }
        }


class AgentErrorResponse(BaseModel):
    """Response model for agent errors"""
    status: str = Field(default="error", description="Always 'error'")
    error_code: str = Field(..., description="Error code for programmatic handling")
    error_message: str = Field(..., description="Human-readable error message")
    timestamp: str = Field(..., description="ISO 8601 timestamp of the error")
    request_id: Optional[str] = Field(None, description="Request ID for logging/debugging")


# ===== Helper Functions =====

async def get_agent():
    """
    Get or initialize the agent instance.
    Uses lazy initialization to defer startup cost.
    
    Returns:
        KraftdAIAgent instance
        
    Raises:
        HTTPException: If agent cannot be initialized
    """
    global _agent_instance
    
    if _agent_instance is not None:
        return _agent_instance
    
    try:
        from agent.kraft_agent import KraftdAIAgent
        
        _agent_instance = await KraftdAIAgent.create()
        logger.info("Agent initialized successfully")
        return _agent_instance
        
    except ImportError:
        logger.error("Agent module not available")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent service not available. Agent module not found."
        )
    except Exception as e:
        logger.error(f"Failed to initialize agent: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to initialize agent: {str(e)}"
        )


def get_current_user_email(authorization: str = Header(None)) -> str:
    """Extract and validate the current user from JWT token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # For MVP, we'll accept any bearer token
    # In production, validate JWT properly
    token = parts[1]
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return "user@example.com"  # MVP: return default user


# ===== Agent API Endpoints =====

@router.post(
    "/analyze",
    response_model=AgentAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a document with AI",
    description="Analyze a document using the Kraftd AI agent. Returns extracted data, risks, and recommendations."
)
async def analyze_document(
    request: AgentAnalyzeRequest,
    authorization: str = Header(None),
    agent = Depends(get_agent)
):
    """
    Analyze a document using the Kraftd AI agent.
    
    The agent will:
    1. Extract key information from the document
    2. Detect potential risks or issues
    3. Provide recommendations for action
    4. Learn from the analysis for future improvements
    
    Args:
        request: AgentAnalyzeRequest with document_id and analysis parameters
        authorization: Bearer token for authentication
        agent: Injected agent instance
    
    Returns:
        AgentAnalyzeResponse with analysis results
    
    Raises:
        HTTPException: For authentication, validation, or processing errors
    """
    request_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    try:
        # Validate authorization
        user_email = get_current_user_email(authorization)
        logger.info(f"[{request_id}] User {user_email} requesting document analysis: {request.document_id}")
        
        # Validate document_id format
        if not request.document_id or len(request.document_id) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document_id: must be at least 3 characters"
            )
        
        # Build analysis prompt
        analysis_prompt = f"""Analyze the document with ID '{request.document_id}'.
Document Type: {request.document_type or 'unknown'}
Analysis Type: {request.analysis_type or 'comprehensive'}
Metadata: {json.dumps(request.metadata or {})}

Provide:
1. Extracted fields and data
2. Identified risks or issues
3. Recommendations for action
4. Confidence assessment"""
        
        # Run agent analysis
        logger.debug(f"[{request_id}] Running agent analysis with prompt: {analysis_prompt[:100]}...")
        response = await agent.run(analysis_prompt)
        
        # Parse response (agent returns JSON string)
        try:
            analysis_result = json.loads(response) if isinstance(response, str) else response
        except json.JSONDecodeError:
            analysis_result = {
                "raw_response": response,
                "status": "partial"
            }
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(f"[{request_id}] Analysis completed in {processing_time:.0f}ms")
        
        return AgentAnalyzeResponse(
            status="success",
            document_id=request.document_id,
            analysis_result=analysis_result,
            confidence_score=0.85,  # TODO: Extract from agent response
            processing_time_ms=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"[{request_id}] Error analyzing document: {str(e)}", exc_info=True)
        
        return AgentAnalyzeResponse(
            status="error",
            document_id=request.document_id,
            analysis_result={},
            processing_time_ms=processing_time,
            timestamp=datetime.now().isoformat(),
            error_message=f"Analysis failed: {str(e)}"
        )


@router.post(
    "/chat",
    response_model=AgentChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with the AI agent",
    description="Send a message to the Kraftd AI agent. Maintains conversation context across messages."
)
async def chat_with_agent(
    request: AgentChatRequest,
    authorization: str = Header(None),
    agent = Depends(get_agent)
):
    """
    Chat with the Kraftd AI agent.
    
    The agent maintains conversation history to provide contextual responses.
    You can ask it to analyze documents, compare data, answer questions, etc.
    
    Args:
        request: AgentChatRequest with message and optional conversation_id
        authorization: Bearer token for authentication
        agent: Injected agent instance
    
    Returns:
        AgentChatResponse with agent's response
    
    Raises:
        HTTPException: For authentication or processing errors
    """
    request_id = str(uuid.uuid4())
    start_time = datetime.now()
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    try:
        # Validate authorization
        user_email = get_current_user_email(authorization)
        logger.info(f"[{request_id}] User {user_email} chatting with agent: conversation_id={conversation_id}")
        
        # Validate message
        if not request.message or len(request.message.strip()) < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty"
            )
        
        # Get conversation history if requested
        history_context = ""
        if request.include_history:
            try:
                history = await agent.get_conversation_history(conversation_id, limit=5)
                if history:
                    history_context = f"\nPrevious messages:\n"
                    for msg in reversed(history[-5:]):
                        history_context += f"- {msg.get('user_message', '')}\n"
            except Exception as e:
                logger.warning(f"[{request_id}] Could not retrieve conversation history: {e}")
        
        # Prepare message with context
        message_with_context = request.message
        if history_context:
            message_with_context = f"{history_context}\nNew message: {request.message}"
        
        # Run agent
        logger.debug(f"[{request_id}] Running agent with message: {request.message[:100]}...")
        response = await agent.run(message_with_context)
        
        # Save conversation
        try:
            await agent._save_conversation(conversation_id, request.message, response, {"user_email": user_email})
        except Exception as e:
            logger.warning(f"[{request_id}] Could not save conversation: {e}")
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(f"[{request_id}] Chat completed in {processing_time:.0f}ms")
        
        return AgentChatResponse(
            status="success",
            conversation_id=conversation_id,
            message=request.message,
            response=response,
            processing_time_ms=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"[{request_id}] Error in chat: {str(e)}", exc_info=True)
        
        return AgentChatResponse(
            status="error",
            conversation_id=conversation_id,
            message=request.message,
            response="",
            processing_time_ms=processing_time,
            timestamp=datetime.now().isoformat(),
            error_message=f"Chat failed: {str(e)}"
        )


@router.get(
    "/status",
    response_model=AgentStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get agent status and capabilities",
    description="Check if the agent is available and see what capabilities it offers."
)
async def get_agent_status(
    authorization: str = Header(None),
    agent = Depends(get_agent)
):
    """
    Get the current status of the Kraftd AI agent.
    
    Returns:
        - Agent availability status
        - Version information
        - Available capabilities and tools
        - Uptime metrics
    
    Args:
        authorization: Bearer token for authentication (optional for status)
        agent: Injected agent instance
    
    Returns:
        AgentStatusResponse with agent status and capabilities
    
    Raises:
        HTTPException: If agent is not available
    """
    try:
        # For status, authorization is optional (allow info endpoint)
        if authorization:
            user_email = get_current_user_email(authorization)
            logger.debug(f"User {user_email} checking agent status")
        
        # Get agent info
        capabilities = [
            "document_analysis",      # Analyze documents for data and risks
            "conversation",            # Multi-turn conversation with context
            "document_intelligence",  # Extract structured data from docs
            "risk_detection",         # Identify potential issues
            "document_learning",      # Learn from document patterns
            "quotation_comparison",   # Compare multiple quotations
            "po_generation",          # Generate purchase orders
            "performance_analytics"   # Track agent performance metrics
        ]
        
        available_tools = [
            "upload_document",
            "extract_intelligence",
            "validate_document",
            "compare_quotations",
            "detect_risks",
            "create_po",
            "learn_from_document_intelligence",
            "get_learned_insights",
            "extract_text_from_image",
            "learn_document_layout",
            "compare_against_adi",
            "get_agent_performance"
        ]
        
        return AgentStatusResponse(
            status="ready",
            version="1.0.0",
            capabilities=capabilities,
            model="gpt-4",
            available_tools=available_tools,
            uptime_seconds=3600.0,  # TODO: Track actual uptime
            message="Agent initialized and ready"
        )
        
    except Exception as e:
        logger.error(f"Error getting agent status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Agent status check failed: {str(e)}"
        )
