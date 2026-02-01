import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Optional, Literal
from pydantic import BaseModel, Field
from .prompts import (
    NARRATIVE_ARCHITECT_PROMPT,
    CHARACTER_DESIGNER_PROMPT,
    MYTHOLOGIST_PROMPT,
    CHAPTER_OUTLINER_PROMPT,
    EDITOR_PROMPT,
    WORLD_BUILDER_PROMPT,
    LOGISTICS_MANAGER_PROMPT
)
from .tools import write_markdown_file

class EditorDecision(BaseModel):
    """The decision of the Editor-in-Chief on whether the story Bible is ready or needs iteration."""
    action: Literal["APPROVE", "REVISE"] = Field(description="APPROVE if the story is consistent and ready, REVISE if changes are needed.")
    critique: Optional[str] = Field(default=None, description="A concise paragraph of feedback if the action is REVISE.")

def init_llm(llm_params: Optional[dict] = None):
    """
    Factory function for LLM instantiation. 
    Follows SRP by only focusing on creating the LLM object.
    """
    params = llm_params or {}
    model_name = params.get("model_name", "gpt-4o")
    temperature = params.get("temperature", 0.7)
    base_url = params.get("base_url", None)
    
    # In a more advanced SOLID implementation, this would use a registry 
    # of providers to stay Open/Closed.
    return ChatOpenAI(
        model=model_name, 
        temperature=temperature,
        base_url=base_url
    )

def get_output_dir(state: dict) -> str:
    """Helper to extract output directory from domain state."""
    return state.get("user_output_dir", "output")

def get_config_params(config: dict) -> dict:
    """Helper to extract infrastructural parameters from LangGraph config."""
    return config.get("configurable", {}) if config else {}

def narrative_architect_agent(state, config=None):
    """Generates the Save the Cat beat sheet."""
    print("--- Narrative Architect ---")
    llm_params = get_config_params(config).get("llm_params")
    llm = init_llm(llm_params)
    
    premise = state.get("premise", "")
    genre = state.get("genre", "")
    additional_info = state.get("additional_info", "")
    critique = state.get("critique", "")

    conversation_context = ""
    if critique:
        conversation_context = f"\n\nIMPORTANT: The Editor has provided the following feedback on the previous draft. You must refine the story to address this:\n{critique}"
    
    user_input_block = f"""
    Premise: {premise}
    Genre: {genre}
    Additional Details:
    {additional_info}
    """
    
    messages = [
        SystemMessage(content=NARRATIVE_ARCHITECT_PROMPT),
        HumanMessage(content=f"Here is the story input:\n{user_input_block}{conversation_context}")
    ]
    
    response = llm.invoke(messages)
    content = response.content
    write_markdown_file("save-the-cat.md", content, get_output_dir(state))
    return {"save_the_cat": content}

def character_designer_agent(state, config=None):
    """Generates character sheets."""
    print("--- Character Designer ---")
    llm_params = get_config_params(config).get("llm_params")
    llm = init_llm(llm_params)

    save_the_cat = state.get("save_the_cat", "")
    critique = state.get("critique", "")

    conversation_context = ""
    if critique:
        conversation_context = f"\n\nIMPORTANT: The Editor has requested changes. Ensure characters align with the refined story and feedback:\n{critique}"
    
    messages = [
        SystemMessage(content=CHARACTER_DESIGNER_PROMPT),
        HumanMessage(content=f"Here is the story structure:\n{save_the_cat}{conversation_context}")
    ]
    
    response = llm.invoke(messages)
    content = response.content
    write_markdown_file("characters.md", content, get_output_dir(state))
    return {"characters": content}

def mythologist_agent(state, config=None):
    """Generates Hero's Journey mapping."""
    print("--- Mythologist ---")
    llm_params = get_config_params(config).get("llm_params")
    llm = init_llm(llm_params)

    save_the_cat = state.get("save_the_cat", "")
    characters = state.get("characters", "")
    critique = state.get("critique", "")
    
    messages = [
        SystemMessage(content=MYTHOLOGIST_PROMPT),
        HumanMessage(content=f"Story Structure:\n{save_the_cat}\n\nCharacters:\n{characters}")
    ]
    
    response = llm.invoke(messages)
    content = response.content
    write_markdown_file("hero-journey.md", content, get_output_dir(state))
    return {"hero_journey": content}

def chapter_outliner_agent(state, config=None):
    """Generates the 27-chapter outline."""
    print("--- Chapter Outliner ---")
    llm_params = get_config_params(config).get("llm_params")
    llm = init_llm(llm_params)

    save_the_cat = state.get("save_the_cat", "")
    hero_journey = state.get("hero_journey", "")
    
    messages = [
        SystemMessage(content=CHAPTER_OUTLINER_PROMPT),
        HumanMessage(content=f"Story Structure:\n{save_the_cat}\n\nHero's Journey:\n{hero_journey}")
    ]
    
    response = llm.invoke(messages)
    content = response.content
    write_markdown_file("chapters.md", content, get_output_dir(state))
    return {"chapters": content}

def editor_agent(state, config=None):
    """Generates Author Notes."""
    print("--- Editor ---")
    llm_params = get_config_params(config).get("llm_params")
    llm = init_llm(llm_params)

    save_the_cat = state.get("save_the_cat", "")
    characters = state.get("characters", "")
    chapters = state.get("chapters", "")
    critique = state.get("critique", "")
    
    messages = [
        SystemMessage(content=EDITOR_PROMPT),
        HumanMessage(content=f"Structure:\n{save_the_cat}\n\nCharacters:\n{characters}\n\nChapters:\n{chapters}")
    ]
    
    response = llm.invoke(messages)
    content = response.content
    write_markdown_file("author-notes.md", content, get_output_dir(state))
    
    return {"author_notes": content}

def editor_critique_agent(state, config=None):
    """
    Structured Node: Reviews the work and decides if iteration is needed using structured output.
    """
    print("--- Editor (Review) ---")
    # Note: max_iterations is a technical param, should be in config too
    max_iter = get_config_params(config).get("max_iterations", 1) 
    current_iter = state.get("iteration", 0)
    
    if current_iter >= max_iter:
        print(f"Max iterations ({max_iter}) reached. Approving.")
        return {"critique": None}

    llm_params = get_config_params(config).get("llm_params")
    llm = init_llm(llm_params)

    save_the_cat = state.get("save_the_cat", "")
    characters = state.get("characters", "")
    lore = state.get("lore", "")
    
    review_prompt = "You are the Editor-in-Chief. Review the Story Bible (Beat Sheet, Characters, Lore) for inconsistencies or clichés."
    
    messages = [
        SystemMessage(content=review_prompt),
        HumanMessage(content=f"BEAT SHEET:\n{save_the_cat}\n\nCHARACTERS:\n{characters}\n\nLORE:\n{lore}")
    ]
    
    structured_llm = llm.with_structured_output(EditorDecision)
    decision = structured_llm.invoke(messages)
    
    if decision.action == "APPROVE":
        print(">>> EDITOR APPROVED.")
        return {"critique": None, "iteration": current_iter + 1}
    else:
        # Extract critique
        print(f"Critique generated: {decision.critique[:100]}...")
        return {"critique": decision.critique, "iteration": current_iter + 1}

def world_builder_agent(state, config=None):
    """Generates World Lore (lore.md). New agent based on feedback."""
    print("--- World Builder (Lore) ---")
    llm_params = get_config_params(config).get("llm_params")
    llm = init_llm(llm_params)

    save_the_cat = state.get("save_the_cat", "")
    characters = state.get("characters", "")
    additional_info = state.get("additional_info", "")

    messages = [
        SystemMessage(content=WORLD_BUILDER_PROMPT),
        HumanMessage(content=f"Structure:\n{save_the_cat}\nCharacters:\n{characters}\nDetails:\n{additional_info}")
    ]

    response = llm.invoke(messages)
    content = response.content
    write_markdown_file("lore.md", content, get_output_dir(state))
    return {"lore": content}

def logistics_manager_agent(state, config=None):
    """Generates Plot Items/Logistics (plot-items.md). Formerly WorldBuilder."""
    print("--- Logistics Manager ---")
    llm_params = get_config_params(config).get("llm_params")
    llm = init_llm(llm_params)

    chapters = state.get("chapters", "")
    lore = state.get("lore", "")
    
    messages = [
        SystemMessage(content=LOGISTICS_MANAGER_PROMPT),
        HumanMessage(content=f"Chapter Outline:\n{chapters}\n\nWorld Lore:\n{lore}")
    ]
    
    response = llm.invoke(messages)
    content = response.content
    write_markdown_file("plot-items.md", content, get_output_dir(state))
    return {"plot_items": content}
