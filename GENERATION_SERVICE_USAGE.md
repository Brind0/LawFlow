# GenerationService Usage Guide

This document demonstrates how to use the `GenerationService` for the human-in-the-loop AI generation workflow.

## Overview

The GenerationService orchestrates the 3-stage generation pipeline (MK1 → MK2 → MK3) with strict unlock requirements:

- **MK1**: Initial summary/extraction - requires LECTURE_PDF
- **MK2**: Detailed structured notes - requires LECTURE_PDF, SOURCE_MATERIAL, TUTORIAL_PDF
- **MK3**: Exam-focused questions - requires all MK2 files + TRANSCRIPT + completed MK2 generation

## Installation

The service is located at `/Users/charliebrind/Documents/university/LawFlow/services/generation_service.py`.

## Basic Usage

### 1. Initialize the Service

```python
from database.connection import get_connection
from services.generation_service import GenerationService
from database.models import Stage

# Get database connection
with get_connection() as conn:
    service = GenerationService(conn)

    # Use service within this context
```

### 2. Check if Topic Can Generate

Before starting a generation, check if all requirements are met:

```python
# Check if MK1 can be generated
can_generate, missing = service.can_generate_stage(topic_id, Stage.MK1)

if can_generate:
    print("Ready to generate MK1!")
else:
    print(f"Cannot generate: {', '.join(missing)}")
    # Output example: "Cannot generate: Missing Lecture Pdf"
```

### 3. Start a Generation

Once requirements are met, start the generation:

```python
try:
    generation = service.start_generation(topic_id, Stage.MK1)

    # The generation is now in PENDING status
    print(f"Generation ID: {generation.id}")
    print(f"Version: {generation.version}")
    print(f"Status: {generation.status.value}")

    # Copy this prompt to Claude
    print("\n--- COPY THIS PROMPT TO CLAUDE ---")
    print(generation.prompt_used)
    print("--- END PROMPT ---\n")

except ValueError as e:
    print(f"Error: {e}")
```

### 4. Update with Claude's Response

After pasting the prompt to Claude and getting a response:

```python
# Paste Claude's response here
claude_response = """
# Easements - Land Law

## Overview
...detailed markdown notes from Claude...
"""

# Update the generation with the response
updated = service.update_generation_response(
    generation_id=generation.id,
    response_content=claude_response
)

print(f"Generation completed! Status: {updated.status.value}")
```

### 5. Mark as Failed (if needed)

If Claude's response was unsatisfactory:

```python
failed = service.mark_generation_failed(generation.id)
print(f"Marked as failed. Can retry with a new generation.")
```

## Complete Workflow Example

### MK1 Generation

```python
from database.connection import get_connection
from services.generation_service import GenerationService
from database.models import Stage

topic_id = "abc-123-def-456"  # Your topic UUID

with get_connection() as conn:
    service = GenerationService(conn)

    # Step 1: Check requirements
    can_gen, missing = service.can_generate_stage(topic_id, Stage.MK1)
    if not can_gen:
        print(f"Missing: {missing}")
        # User needs to upload LECTURE_PDF first
        exit()

    # Step 2: Start generation
    gen = service.start_generation(topic_id, Stage.MK1)
    print(f"Copy this to Claude:\n{gen.prompt_used}")

    # Step 3: User manually pastes prompt to Claude, gets response

    # Step 4: Update with response
    claude_response = input("Paste Claude's response: ")
    service.update_generation_response(gen.id, claude_response)

    print("MK1 complete!")
```

### MK2 Generation

```python
with get_connection() as conn:
    service = GenerationService(conn)

    # MK2 requires LECTURE_PDF, SOURCE_MATERIAL, TUTORIAL_PDF
    can_gen, missing = service.can_generate_stage(topic_id, Stage.MK2)
    if not can_gen:
        print(f"Cannot generate MK2. Missing: {missing}")
        exit()

    gen = service.start_generation(topic_id, Stage.MK2)
    print(f"MK2 Prompt:\n{gen.prompt_used}")

    # ... same workflow as MK1
```

### MK3 Generation

```python
with get_connection() as conn:
    service = GenerationService(conn)

    # MK3 requires all MK2 files + TRANSCRIPT + completed MK2
    can_gen, missing = service.can_generate_stage(topic_id, Stage.MK3)
    if not can_gen:
        print(f"Cannot generate MK3. Missing: {missing}")
        # Common issue: "Missing completed MK2 generation"
        exit()

    gen = service.start_generation(topic_id, Stage.MK3)

    # Note: The prompt includes MK2's response content automatically
    # as `previous_content` in the template
    print(f"MK3 Prompt:\n{gen.prompt_used}")

    # ... same workflow
```

## Viewing Generation History

```python
with get_connection() as conn:
    service = GenerationService(conn)

    # Get all generations for a topic
    all_gens = service.get_generation_history(topic_id)
    for gen in all_gens:
        print(f"{gen.stage.value} v{gen.version} - {gen.status.value}")

    # Get only MK1 generations
    mk1_gens = service.get_generation_history(topic_id, Stage.MK1)

    # Get latest completed generation
    latest_mk2 = service.get_latest_completed_generation(topic_id, Stage.MK2)
    if latest_mk2:
        print(f"Latest MK2: Version {latest_mk2.version}")
```

## Stage Unlock Requirements Summary

| Stage | Required Files | Additional Requirements |
|-------|---------------|------------------------|
| MK1   | LECTURE_PDF | None |
| MK2   | LECTURE_PDF, SOURCE_MATERIAL, TUTORIAL_PDF | None |
| MK3   | LECTURE_PDF, SOURCE_MATERIAL, TUTORIAL_PDF, TRANSCRIPT | Completed MK2 generation |

## Error Handling

The service raises `ValueError` when:
- Requirements are not met
- Topic or module not found
- MK3 attempted without completed MK2

Always wrap service calls in try-except:

```python
try:
    gen = service.start_generation(topic_id, Stage.MK1)
except ValueError as e:
    print(f"Error: {e}")
    # Handle error appropriately
```

## Integration with UI

The GenerationService is designed to be called from Streamlit UI components:

```python
# In ui/components/generation_modal.py (to be created)

import streamlit as st
from services.generation_service import GenerationService

def show_generation_modal(conn, topic_id, stage):
    service = GenerationService(conn)

    # Check if can generate
    can_gen, missing = service.can_generate_stage(topic_id, stage)

    if not can_gen:
        st.error(f"Cannot generate {stage.value}:")
        for req in missing:
            st.error(f"- {req}")
        return

    # Show start button
    if st.button(f"Start {stage.value} Generation"):
        gen = service.start_generation(topic_id, stage)
        st.session_state['current_generation'] = gen

        # Show prompt with copy button
        st.text_area("Prompt", gen.prompt_used, height=300)
        # Copy button implementation in clipboard.py

    # Show paste area if generation is pending
    if 'current_generation' in st.session_state:
        response = st.text_area("Paste Claude's response here")
        if st.button("Submit Response"):
            service.update_generation_response(
                st.session_state['current_generation'].id,
                response
            )
            st.success("Generation completed!")
```

## Testing

The service includes comprehensive unit tests at:
`/Users/charliebrind/Documents/university/LawFlow/tests/test_generation_service.py`

Run tests with:
```bash
pytest tests/test_generation_service.py -v
```

All 14 tests pass successfully, covering:
- Stage unlock logic for all stages
- Generation creation and versioning
- MK3 integration with MK2 content
- Generation history tracking
- Response updates and failure handling
