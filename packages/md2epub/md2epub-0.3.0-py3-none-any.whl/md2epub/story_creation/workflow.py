from typing import TypedDict, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from .agents import (
    narrative_architect_agent,
    character_designer_agent,
    mythologist_agent,
    chapter_outliner_agent,
    editor_agent,
    editor_critique_agent,
    world_builder_agent,
    logistics_manager_agent
)

class StoryState(TypedDict):
    # Inputs
    premise: str
    genre: str
    additional_info: str
    user_output_dir: str
    
    # Process tracking (Domain data: which refinement pass we are on)
    iteration: int
    
    # Outputs
    save_the_cat: Optional[str]
    characters: Optional[str]
    hero_journey: Optional[str]
    chapters: Optional[str]
    author_notes: Optional[str]
    lore: Optional[str]
    plot_items: Optional[str]
    
    # Feedback
    critique: Optional[str]

def should_iterate(state: StoryState):
    """Condition to determine whether to loop back or finish."""
    critique = state.get("critique")
    
    # If there is a critique, and we haven't hit max iterations (logic handled in agent, but safe check here)
    # Actually, the agent sets critique=None if max iterations reached.
    if critique:
        return "retry"
    return "continue"

def create_story_graph():
    """Creates the LangGraph workflow for story creation."""
    workflow = StateGraph(StoryState)

    # Add nodes
    workflow.add_node("NarrativeArchitect", narrative_architect_agent)
    workflow.add_node("CharacterDesigner", character_designer_agent)
    workflow.add_node("WorldBuilder", world_builder_agent) 
    workflow.add_node("Mythologist", mythologist_agent)
    workflow.add_node("ChapterOutliner", chapter_outliner_agent)
    workflow.add_node("Editor", editor_agent) # Writes author notes
    workflow.add_node("EditorCritique", editor_critique_agent) # Decides if valid
    workflow.add_node("LogisticsManager", logistics_manager_agent)

    # Define edges (Sequential Flow)
    # Narrative -> Character -> WorldBuilder -> Mythologist -> Chapter -> Editor -> EditorCritique
    
    workflow.set_entry_point("NarrativeArchitect")
    
    workflow.add_edge("NarrativeArchitect", "CharacterDesigner")
    workflow.add_edge("CharacterDesigner", "WorldBuilder")
    workflow.add_edge("WorldBuilder", "Mythologist")
    workflow.add_edge("Mythologist", "ChapterOutliner")
    workflow.add_edge("ChapterOutliner", "Editor")
    workflow.add_edge("Editor", "EditorCritique")
    
    # Conditional Edge
    workflow.add_conditional_edges(
        "EditorCritique",
        should_iterate,
        {
            "retry": "NarrativeArchitect",
            "continue": "LogisticsManager"
        }
    )
    
    workflow.add_edge("LogisticsManager", END)

    return workflow.compile()
