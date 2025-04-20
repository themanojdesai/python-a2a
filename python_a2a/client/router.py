"""
AI-driven router for selecting the optimal agent based on query semantics.
"""

import json
from typing import Dict, List, Any, Optional, Tuple, Union

from ..models import Message, TextContent, MessageRole
from .base import BaseA2AClient


class AIAgentRouter:
    """
    Uses an LLM to intelligently route queries to the most appropriate agent.
    
    This router analyzes the query and conversation context to determine
    which agent in the network is best suited to handle the request.
    Token usage is optimized by using concise prompts and caching agent descriptions.
    """
    
    def __init__(
        self, 
        llm_client: BaseA2AClient,
        agent_network: 'AgentNetwork',
        system_prompt: Optional[str] = None,
        max_history_tokens: int = 500
    ):
        """
        Initialize the AI agent router.
        
        Args:
            llm_client: LLM client for making routing decisions
            agent_network: Network of available agents
            system_prompt: Custom system prompt for the router
            max_history_tokens: Maximum tokens to include from conversation history
        """
        self.llm = llm_client
        self.agent_network = agent_network
        self.agent_descriptions = self._gather_agent_descriptions()
        self.max_history_tokens = max_history_tokens
        self.system_prompt = system_prompt or self._create_default_system_prompt()
        
        # Cache for agent selection to avoid repeated LLM calls for similar queries
        self._selection_cache = {}
        
    def _create_default_system_prompt(self) -> str:
        """Create a default system prompt for the router."""
        return (
            "You are an agent router that determines which specialized agent "
            "should handle a user query. Analyze the query's intent and select "
            "the most appropriate agent based on its capabilities. Respond with "
            "only the agent name, nothing else."
        )
    
    def _gather_agent_descriptions(self) -> Dict[str, Dict[str, Any]]:
        """Collect concise descriptions and capabilities from all agents."""
        descriptions = {}
        
        for name, agent in self.agent_network.agents.items():
            # Extract only essential information to keep the prompt small
            try:
                agent_card = getattr(agent, 'agent_card', None)
                if agent_card:
                    descriptions[name] = {
                        "description": agent_card.description,
                        "skills": [{"name": skill.name, "description": skill.description} 
                                 for skill in agent_card.skills[:3]],  # Limit to top 3 skills
                        "tags": list(set(tag for skill in agent_card.skills 
                                      for tag in skill.tags[:5]))  # Limit tags, remove duplicates
                    }
                else:
                    # Fallback for agents without cards
                    descriptions[name] = {
                        "description": f"Agent '{name}' for general queries",
                        "skills": [],
                        "tags": []
                    }
            except Exception as e:
                # Handle any errors gracefully
                descriptions[name] = {
                    "description": f"Agent '{name}' (details unavailable)",
                    "skills": [],
                    "tags": []
                }
                
        return descriptions
    
    def _create_routing_prompt(self, query: str, conversation_history: Optional[List[Dict]] = None) -> str:
        """
        Create an efficient prompt for the router LLM.
        
        Args:
            query: The user query to route
            conversation_history: Optional conversation history for context
        
        Returns:
            A concise prompt for the LLM
        """
        # Create a compact description of available agents
        agent_descriptions = "\n".join([
            f"Agent: {name}\nDescription: {info['description']}\n"
            f"Skills: {', '.join(skill['name'] for skill in info['skills'])}\n"
            f"Tags: {', '.join(info['tags'])}"
            for name, info in self.agent_descriptions.items()
        ])
        
        # Include truncated history if provided
        history_text = ""
        if conversation_history:
            # Only include the most recent and relevant messages
            recent_history = conversation_history[-3:]  # Last 3 messages maximum
            history_text = "\nRecent conversation:\n" + "\n".join([
                f"{'User' if msg.get('role') == 'user' else 'Agent'}: {msg.get('content', {}).get('text', '')}"
                for msg in recent_history
                if isinstance(msg, dict) and 'role' in msg and 'content' in msg
            ])
        
        # Construct the final prompt
        prompt = (
            f"Available Agents:\n{agent_descriptions}\n\n"
            f"User Query: {query}\n{history_text}\n\n"
            "Which agent should handle this query? Respond with just the agent name."
        )
        
        return prompt
    
    def _parse_agent_selection(self, response: str) -> str:
        """
        Parse the LLM's response to extract the selected agent name.
        
        Args:
            response: The LLM's response text
            
        Returns:
            The name of the selected agent
        """
        # Clean up response and extract just the agent name
        agent_name = response.strip().lower()
        
        # Handle multi-line responses by taking the first line
        if "\n" in agent_name:
            agent_name = agent_name.split("\n")[0].strip()
        
        # Remove common prefixes that LLMs might add
        for prefix in ["agent:", "agent name:", "the agent", "i recommend", "recommended agent:"]:
            if agent_name.startswith(prefix):
                agent_name = agent_name[len(prefix):].strip()
        
        # Remove quotes if present
        agent_name = agent_name.strip('"\'')
        
        # Check if this matches any of our agent names (case-insensitive)
        for name in self.agent_descriptions:
            if name.lower() == agent_name or name.lower() in agent_name:
                return name
        
        # If no exact match, try to find the closest match
        for name in self.agent_descriptions:
            if name.lower() in agent_name or agent_name in name.lower():
                return name
        
        # Default to the first agent if no match found
        if self.agent_descriptions:
            return next(iter(self.agent_descriptions.keys()))
        
        # Last resort
        return agent_name
    
    def route_query(
        self, 
        query: str, 
        conversation_history: Optional[List[Dict]] = None,
        use_cache: bool = True
    ) -> Tuple[str, float]:
        """
        Route a query to the most appropriate agent.
        
        Args:
            query: The query to route
            conversation_history: Optional conversation history for context
            use_cache: Whether to use cached results for similar queries
            
        Returns:
            A tuple of (agent_name, confidence_score)
        """
        # Check cache for similar queries to save tokens
        if use_cache:
            cache_key = query.lower().strip()
            if cache_key in self._selection_cache:
                return self._selection_cache[cache_key]
        
        # Create the routing prompt
        prompt = self._create_routing_prompt(query, conversation_history)
        
        # Ask LLM to select the best agent
        message = Message(
            content=TextContent(text=prompt),
            role=MessageRole.USER
        )
        
        try:
            response = self.llm.send_message(message)
            agent_name = self._parse_agent_selection(response.content.text)
            confidence = 0.9  # Default confidence score
            
            # Store in cache
            if use_cache:
                self._selection_cache[query.lower().strip()] = (agent_name, confidence)
            
            return agent_name, confidence
            
        except Exception as e:
            # Fallback logic in case of LLM failure
            # Use basic keyword matching as a backup
            return self._fallback_routing(query)
    
    def _fallback_routing(self, query: str) -> Tuple[str, float]:
        """
        Fallback method to route queries when LLM fails.
        Uses basic keyword matching against agent descriptions.
        
        Args:
            query: The query to route
            
        Returns:
            A tuple of (agent_name, confidence_score)
        """
        query_lower = query.lower()
        best_match = None
        best_score = 0
        
        for name, info in self.agent_descriptions.items():
            score = 0
            
            # Check description
            if any(keyword in query_lower for keyword in info['description'].lower().split()):
                score += 1
                
            # Check skill names and descriptions
            for skill in info['skills']:
                if skill['name'].lower() in query_lower:
                    score += 2
                if any(keyword in query_lower for keyword in skill['description'].lower().split()):
                    score += 1
            
            # Check tags
            for tag in info['tags']:
                if tag.lower() in query_lower:
                    score += 3
            
            if score > best_score:
                best_score = score
                best_match = name
        
        # If no good match, return the first agent
        if best_match is None and self.agent_descriptions:
            best_match = next(iter(self.agent_descriptions.keys()))
            best_score = 0
        
        # Normalize score to a confidence value between 0 and 1
        max_possible_score = 10  # Approximate maximum possible score
        confidence = min(best_score / max_possible_score, 1.0) if best_score > 0 else 0.1
        
        return best_match, confidence