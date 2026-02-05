"""
Sequential Thinking MCP Server

Provides guided reasoning chain tools for methodology transparency.
Manages reasoning state throughout investigation workflows.
"""

from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime
from dataclasses import dataclass, field

from backend.mcp_servers.base_mcp_server import MCPServerBase, MCPTool
from backend.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ReasoningStep:
    """A single step in a reasoning chain."""
    step_number: int
    phase: str
    action: str
    evidence: List[str]
    reasoning: str
    conclusion: str
    confidence: int  # 0-100
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step": self.step_number,
            "phase": self.phase,
            "action": self.action,
            "evidence": self.evidence,
            "reasoning": self.reasoning,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "timestamp": self.timestamp
        }


@dataclass
class ReasoningChain:
    """Complete reasoning chain for an investigation."""
    chain_id: str
    question: str
    reasoning_type: str
    steps: List[ReasoningStep] = field(default_factory=list)
    status: str = "active"  # active, finalized, abandoned
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finalized_at: Optional[str] = None
    final_conclusion: Optional[str] = None
    overall_confidence: Optional[int] = None

    def add_step(self, step: ReasoningStep) -> None:
        """Add a step to the chain."""
        step.step_number = len(self.steps) + 1
        self.steps.append(step)

    def finalize(self, conclusion: str, confidence: int) -> None:
        """Finalize the reasoning chain."""
        self.status = "finalized"
        self.finalized_at = datetime.now().isoformat()
        self.final_conclusion = conclusion
        self.overall_confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chain_id": self.chain_id,
            "question": self.question,
            "reasoning_type": self.reasoning_type,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status,
            "created_at": self.created_at,
            "finalized_at": self.finalized_at,
            "final_conclusion": self.final_conclusion,
            "overall_confidence": self.overall_confidence,
            "step_count": len(self.steps)
        }


class SequentialThinkingMCPServer(MCPServerBase):
    """
    MCP server for managing reasoning chains.

    Provides tools for:
    - Starting a reasoning chain for a question
    - Adding steps with evidence and conclusions
    - Finalizing chains with overall assessment

    The reasoning chain state is maintained in memory and can be
    persisted with investigation results.
    """

    def __init__(self):
        """Initialize the Sequential Thinking MCP server."""
        super().__init__("sequential_thinking")

        # In-memory storage for active reasoning chains
        self._chains: Dict[str, ReasoningChain] = {}

        # Register tools
        self._register_tools()

        logger.info("SequentialThinkingMCPServer initialized")

    def _register_tools(self):
        """Register available tools."""
        self.tools = {
            "start_reasoning_chain": MCPTool(
                name="start_reasoning_chain",
                description="Initialize a new reasoning chain for an investigation question. Returns a chain_id to use for adding steps.",
                parameters={
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The question or decision being reasoned about"
                        },
                        "reasoning_type": {
                            "type": "string",
                            "description": "Type of reasoning (identification, location, confidence, recommendation)",
                            "enum": ["identification", "location", "confidence", "recommendation", "match_selection", "quality_assessment"]
                        },
                        "context": {
                            "type": "object",
                            "description": "Optional context for the reasoning",
                            "default": {}
                        }
                    },
                    "required": ["question", "reasoning_type"]
                },
                handler=self._handle_start_chain
            ),
            "add_reasoning_step": MCPTool(
                name="add_reasoning_step",
                description="Add a step to an existing reasoning chain with evidence, reasoning, and conclusion.",
                parameters={
                    "type": "object",
                    "properties": {
                        "chain_id": {
                            "type": "string",
                            "description": "The ID of the reasoning chain"
                        },
                        "phase": {
                            "type": "string",
                            "description": "The investigation phase this step belongs to"
                        },
                        "action": {
                            "type": "string",
                            "description": "What action was taken in this step"
                        },
                        "evidence": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of evidence items supporting this step"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "Explanation of the reasoning process"
                        },
                        "conclusion": {
                            "type": "string",
                            "description": "Conclusion reached in this step"
                        },
                        "confidence": {
                            "type": "integer",
                            "description": "Confidence level (0-100) in this step's conclusion",
                            "minimum": 0,
                            "maximum": 100
                        }
                    },
                    "required": ["chain_id", "phase", "action", "evidence", "reasoning", "conclusion", "confidence"]
                },
                handler=self._handle_add_step
            ),
            "finalize_reasoning": MCPTool(
                name="finalize_reasoning",
                description="Finalize a reasoning chain with overall conclusion and confidence.",
                parameters={
                    "type": "object",
                    "properties": {
                        "chain_id": {
                            "type": "string",
                            "description": "The ID of the reasoning chain to finalize"
                        },
                        "final_conclusion": {
                            "type": "string",
                            "description": "The overall conclusion reached"
                        },
                        "overall_confidence": {
                            "type": "integer",
                            "description": "Overall confidence level (0-100)",
                            "minimum": 0,
                            "maximum": 100
                        },
                        "supporting_factors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Factors supporting the conclusion",
                            "default": []
                        },
                        "uncertainty_factors": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Factors causing uncertainty",
                            "default": []
                        }
                    },
                    "required": ["chain_id", "final_conclusion", "overall_confidence"]
                },
                handler=self._handle_finalize
            ),
            "get_reasoning_chain": MCPTool(
                name="get_reasoning_chain",
                description="Retrieve the current state of a reasoning chain.",
                parameters={
                    "type": "object",
                    "properties": {
                        "chain_id": {
                            "type": "string",
                            "description": "The ID of the reasoning chain"
                        }
                    },
                    "required": ["chain_id"]
                },
                handler=self._handle_get_chain
            ),
            "list_active_chains": MCPTool(
                name="list_active_chains",
                description="List all active (non-finalized) reasoning chains.",
                parameters={
                    "type": "object",
                    "properties": {}
                },
                handler=self._handle_list_chains
            )
        }

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        return [tool.to_dict() for tool in self.tools.values()]

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool."""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not found"}

        try:
            return await self.tools[tool_name].call(arguments)
        except Exception as e:
            logger.error(f"Tool call failed: {tool_name}", error=str(e), exc_info=True)
            return {"error": str(e)}

    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources."""
        return []

    async def _handle_start_chain(
        self,
        question: str,
        reasoning_type: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Handle starting a new reasoning chain."""
        try:
            chain_id = str(uuid.uuid4())[:8]

            chain = ReasoningChain(
                chain_id=chain_id,
                question=question,
                reasoning_type=reasoning_type
            )

            self._chains[chain_id] = chain

            logger.info(f"Started reasoning chain: {chain_id} for '{question[:50]}...'")

            return {
                "success": True,
                "chain_id": chain_id,
                "question": question,
                "reasoning_type": reasoning_type,
                "status": "active",
                "message": "Reasoning chain started. Use add_reasoning_step to add steps."
            }

        except Exception as e:
            logger.error(f"Failed to start reasoning chain: {e}")
            return {"error": str(e), "success": False}

    async def _handle_add_step(
        self,
        chain_id: str,
        phase: str,
        action: str,
        evidence: List[str],
        reasoning: str,
        conclusion: str,
        confidence: int
    ) -> Dict[str, Any]:
        """Handle adding a step to a reasoning chain."""
        try:
            if chain_id not in self._chains:
                return {"error": f"Chain {chain_id} not found", "success": False}

            chain = self._chains[chain_id]

            if chain.status != "active":
                return {"error": f"Chain {chain_id} is {chain.status}, cannot add steps", "success": False}

            step = ReasoningStep(
                step_number=0,  # Will be set by add_step
                phase=phase,
                action=action,
                evidence=evidence,
                reasoning=reasoning,
                conclusion=conclusion,
                confidence=confidence
            )

            chain.add_step(step)

            logger.info(f"Added step {step.step_number} to chain {chain_id}")

            return {
                "success": True,
                "chain_id": chain_id,
                "step_number": step.step_number,
                "phase": phase,
                "confidence": confidence,
                "total_steps": len(chain.steps),
                "message": f"Step {step.step_number} added to reasoning chain."
            }

        except Exception as e:
            logger.error(f"Failed to add reasoning step: {e}")
            return {"error": str(e), "success": False}

    async def _handle_finalize(
        self,
        chain_id: str,
        final_conclusion: str,
        overall_confidence: int,
        supporting_factors: Optional[List[str]] = None,
        uncertainty_factors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Handle finalizing a reasoning chain."""
        try:
            if chain_id not in self._chains:
                return {"error": f"Chain {chain_id} not found", "success": False}

            chain = self._chains[chain_id]

            if chain.status != "active":
                return {"error": f"Chain {chain_id} is already {chain.status}", "success": False}

            chain.finalize(final_conclusion, overall_confidence)

            logger.info(f"Finalized chain {chain_id} with confidence {overall_confidence}%")

            # Build summary
            summary = {
                "success": True,
                "chain_id": chain_id,
                "question": chain.question,
                "reasoning_type": chain.reasoning_type,
                "total_steps": len(chain.steps),
                "final_conclusion": final_conclusion,
                "overall_confidence": overall_confidence,
                "supporting_factors": supporting_factors or [],
                "uncertainty_factors": uncertainty_factors or [],
                "status": "finalized",
                "message": "Reasoning chain finalized successfully."
            }

            # Calculate step confidence progression
            if chain.steps:
                confidences = [s.confidence for s in chain.steps]
                summary["confidence_progression"] = {
                    "start": confidences[0],
                    "end": confidences[-1],
                    "min": min(confidences),
                    "max": max(confidences),
                    "average": sum(confidences) / len(confidences)
                }

            return summary

        except Exception as e:
            logger.error(f"Failed to finalize reasoning chain: {e}")
            return {"error": str(e), "success": False}

    async def _handle_get_chain(self, chain_id: str) -> Dict[str, Any]:
        """Handle getting a reasoning chain."""
        try:
            if chain_id not in self._chains:
                return {"error": f"Chain {chain_id} not found", "success": False}

            chain = self._chains[chain_id]
            return {
                "success": True,
                "chain": chain.to_dict()
            }

        except Exception as e:
            logger.error(f"Failed to get reasoning chain: {e}")
            return {"error": str(e), "success": False}

    async def _handle_list_chains(self) -> Dict[str, Any]:
        """Handle listing active chains."""
        try:
            active_chains = [
                {
                    "chain_id": chain.chain_id,
                    "question": chain.question[:50] + "..." if len(chain.question) > 50 else chain.question,
                    "reasoning_type": chain.reasoning_type,
                    "status": chain.status,
                    "step_count": len(chain.steps),
                    "created_at": chain.created_at
                }
                for chain in self._chains.values()
                if chain.status == "active"
            ]

            return {
                "success": True,
                "active_chains": active_chains,
                "count": len(active_chains)
            }

        except Exception as e:
            logger.error(f"Failed to list chains: {e}")
            return {"error": str(e), "success": False}

    def get_chain(self, chain_id: str) -> Optional[ReasoningChain]:
        """Get a chain by ID (for external use)."""
        return self._chains.get(chain_id)

    def get_chain_as_reasoning_steps(self, chain_id: str) -> List[Dict[str, Any]]:
        """
        Get a chain formatted as reasoning_steps for Investigation2State.

        This format matches the existing reasoning_steps structure.
        """
        chain = self._chains.get(chain_id)
        if not chain:
            return []

        steps = []
        for step in chain.steps:
            steps.append({
                "step": step.step_number,
                "phase": step.phase,
                "action": step.action,
                "reasoning": step.reasoning,
                "evidence": step.evidence,
                "conclusion": step.conclusion,
                "confidence": step.confidence
            })

        return steps

    def clear_chain(self, chain_id: str) -> bool:
        """Clear a chain from memory."""
        if chain_id in self._chains:
            del self._chains[chain_id]
            return True
        return False

    # Convenience methods for direct workflow integration
    async def start_reasoning_chain(
        self,
        question: str,
        context: Optional[Dict] = None,
        reasoning_type: str = "investigation"
    ) -> Dict[str, Any]:
        """
        Convenience method to start a reasoning chain.
        Wraps _handle_start_chain for direct workflow use.
        """
        return await self._handle_start_chain(
            question=question,
            reasoning_type=reasoning_type,
            context=context
        )

    async def add_reasoning_step(
        self,
        chain_id: str,
        evidence: List[str],
        reasoning: str,
        conclusion: str,
        confidence: int,
        phase: str = "analysis",
        action: str = "Analyzing evidence"
    ) -> Dict[str, Any]:
        """
        Convenience method to add a reasoning step.
        Wraps _handle_add_step for direct workflow use.
        """
        return await self._handle_add_step(
            chain_id=chain_id,
            phase=phase,
            action=action,
            evidence=evidence,
            reasoning=reasoning,
            conclusion=conclusion,
            confidence=confidence
        )

    async def finalize_reasoning(self, chain_id: str) -> Dict[str, Any]:
        """
        Convenience method to finalize a reasoning chain.
        Auto-generates conclusion and confidence from steps.
        """
        chain = self._chains.get(chain_id)
        if not chain or not chain.steps:
            return await self._handle_finalize(
                chain_id=chain_id,
                final_conclusion="No steps recorded",
                overall_confidence=0
            )

        # Calculate weighted confidence from steps
        total_conf = sum(s.confidence for s in chain.steps)
        avg_conf = total_conf // len(chain.steps) if chain.steps else 50

        # Build final conclusion from last few steps
        recent_conclusions = [s.conclusion for s in chain.steps[-3:]]
        final_conclusion = " → ".join(recent_conclusions)

        return await self._handle_finalize(
            chain_id=chain_id,
            final_conclusion=final_conclusion,
            overall_confidence=avg_conf
        )


# Singleton instance
_server_instance: Optional[SequentialThinkingMCPServer] = None


def get_sequential_thinking_server() -> SequentialThinkingMCPServer:
    """Get or create the singleton server instance."""
    global _server_instance
    if _server_instance is None:
        _server_instance = SequentialThinkingMCPServer()
    return _server_instance
