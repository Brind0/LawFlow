# GenerationService Architecture

## Overview

The GenerationService is the core orchestration layer for LawFlow's human-in-the-loop AI generation pipeline.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         UI Layer (Streamlit)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Generation Modal Component                               │  │
│  │  - Check requirements button                              │  │
│  │  - Start generation button                                │  │
│  │  - Prompt display with copy button (clipboard.py)         │  │
│  │  - Response paste area                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              GenerationService                            │  │
│  │                                                           │  │
│  │  Methods:                                                 │  │
│  │  • can_generate_stage(topic_id, stage)                   │  │
│  │    → Returns (bool, List[missing_requirements])          │  │
│  │                                                           │  │
│  │  • start_generation(topic_id, stage)                     │  │
│  │    → Creates pending Generation with prompt              │  │
│  │                                                           │  │
│  │  • update_generation_response(gen_id, response)          │  │
│  │    → Marks generation as COMPLETED                       │  │
│  │                                                           │  │
│  │  • get_generation_history(topic_id, stage?)              │  │
│  │    → Returns List[Generation]                            │  │
│  │                                                           │  │
│  │  • mark_generation_failed(gen_id)                        │  │
│  │                                                           │  │
│  │  • get_latest_completed_generation(topic_id, stage)      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              PromptService                                │  │
│  │  • build_prompt(stage, topic, module, files, prev)       │  │
│  │  • get_required_files_for_stage(stage)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Repository Layer                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  GenerationRepo  │  │   ContentRepo    │  │  TopicRepo   │ │
│  │  ModuleRepo      │  │                  │  │              │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Database (SQLite)                           │
│  Tables: modules, topics, content_items, generations            │
└─────────────────────────────────────────────────────────────────┘
```

## Stage Unlock Logic Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    can_generate_stage(topic_id, stage)           │
└──────────────────────────────────────────────────────────────────┘
                              ↓
                  ┌───────────────────────┐
                  │   Which Stage?        │
                  └───────────────────────┘
                   ↓           ↓          ↓
           ┌───────┐    ┌──────┐    ┌─────────┐
           │  MK1  │    │  MK2 │    │   MK3   │
           └───────┘    └──────┘    └─────────┘
                ↓            ↓             ↓
      ┌─────────────┐  ┌──────────┐  ┌──────────────────┐
      │ LECTURE_PDF │  │ MK1 +    │  │ MK2 +            │
      │             │  │ SOURCE + │  │ TRANSCRIPT +     │
      │             │  │ TUTORIAL │  │ COMPLETED_MK2    │
      └─────────────┘  └──────────┘  └──────────────────┘
                ↓            ↓             ↓
           [Check Content]  [Check Content]  [Check Content + Gen]
                ↓            ↓             ↓
      ┌─────────────────────────────────────────────┐
      │  Return (can_generate, missing_requirements) │
      └─────────────────────────────────────────────┘
```

## Generation Workflow Sequence

```
1. USER ACTION: Click "Generate MK1"
   ↓
2. UI: Call service.can_generate_stage(topic_id, Stage.MK1)
   ↓
3. SERVICE: Check if LECTURE_PDF uploaded
   ├─ NO  → Return (False, ["Missing Lecture Pdf"])
   │        UI shows error
   │
   └─ YES → Return (True, [])
            ↓
4. UI: Enable "Start Generation" button
   ↓
5. USER ACTION: Click "Start Generation"
   ↓
6. UI: Call service.start_generation(topic_id, Stage.MK1)
   ↓
7. SERVICE ORCHESTRATION:
   a) Validate requirements (redundant check)
   b) Fetch topic info from TopicRepo
   c) Fetch module info from ModuleRepo
   d) Fetch content file names from ContentRepo
   e) For MK3: Fetch MK2 response_content
   f) Call prompt_service.build_prompt(...)
   g) Get next version number
   h) Create Generation object (status=PENDING)
   i) Save to database via GenerationRepo
   j) Return Generation object
   ↓
8. UI: Display prompt with copy button
   ↓
9. USER ACTION: Copy prompt, paste to Claude Projects, get response
   ↓
10. USER ACTION: Paste response back to UI
    ↓
11. UI: Call service.update_generation_response(gen_id, response)
    ↓
12. SERVICE: Update generation.status = COMPLETED
            Save response_content to database
    ↓
13. UI: Show success, unlock next stage if applicable
```

## MK3 Special Case: Previous Content Integration

```
┌─────────────────────────────────────────────────────────────────┐
│              start_generation(topic_id, Stage.MK3)               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
              ┌───────────────────────────────┐
              │ Get completed MK2 generations │
              │ (ordered by version DESC)     │
              └───────────────────────────────┘
                              ↓
                  ┌─────────────────────┐
                  │ Take latest (v. 2)  │
                  │ previous_content =  │
                  │   mk2.response_content
                  │ previous_gen_id =   │
                  │   mk2.id            │
                  └─────────────────────┘
                              ↓
              ┌───────────────────────────────┐
              │ prompt_service.build_prompt(  │
              │   stage=MK3,                  │
              │   topic_name="Easements",     │
              │   module_name="Land Law",     │
              │   file_names=[...],           │
              │   previous_content=mk2_text   │ ← Included!
              │ )                              │
              └───────────────────────────────┘
                              ↓
              ┌───────────────────────────────┐
              │ Jinja2 template renders with: │
              │ {{ previous_content }}        │
              │                               │
              │ Result: MK3 prompt contains   │
              │ full MK2 notes for context    │
              └───────────────────────────────┘
```

## Versioning System

```
Topic: "Easements" (id: abc-123)

Generations Table:
┌──────┬──────────┬───────┬─────────┬──────────┬─────────────────┐
│  ID  │ Topic_ID │ Stage │ Version │  Status  │ Response_Content│
├──────┼──────────┼───────┼─────────┼──────────┼─────────────────┤
│ g1   │ abc-123  │ MK1   │    1    │ COMPLETED│ "First attempt" │
│ g2   │ abc-123  │ MK1   │    2    │ COMPLETED│ "Better notes"  │ ← Latest MK1
│ g3   │ abc-123  │ MK2   │    1    │ FAILED   │ NULL            │
│ g4   │ abc-123  │ MK2   │    2    │ COMPLETED│ "Detailed..."   │ ← Latest MK2
│ g5   │ abc-123  │ MK3   │    1    │ PENDING  │ NULL            │
└──────┴──────────┴───────┴─────────┴──────────┴─────────────────┘

When MK3 (g5) is started:
- previous_generation_id = g4 (latest completed MK2)
- previous_content = g4.response_content
```

## Key Design Decisions

### 1. Human-in-the-Loop (Not Automated)
**Decision**: GenerationService does NOT call Claude API directly.

**Rationale**:
- Minimize API costs
- User maintains control over quality
- Leverages Claude Projects for context management
- Allows manual prompt refinement if needed

### 2. Strict Stage Unlocking
**Decision**: MK3 requires COMPLETED MK2, not just PENDING.

**Rationale**:
- Ensures MK2 content is available for prompt context
- Prevents generating exam questions without detailed notes
- Enforces quality control workflow

### 3. Soft Generation Failure
**Decision**: mark_generation_failed() doesn't delete, just changes status.

**Rationale**:
- Preserves audit trail
- Allows comparing failed vs successful attempts
- User can see what didn't work

### 4. Stateless Service
**Decision**: Service has no instance state except repository references.

**Rationale**:
- Safe for concurrent access
- No session management complexity
- Fits Streamlit's rerun model

## Dependencies

```
GenerationService
  ├─ GenerationRepository
  ├─ ContentRepository
  ├─ TopicRepository
  ├─ ModuleRepository
  └─ PromptService
       └─ Jinja2 + YAML templates
```

## File Locations

- **Service**: `/services/generation_service.py`
- **Tests**: `/tests/test_generation_service.py`
- **Usage Guide**: `/GENERATION_SERVICE_USAGE.md`
- **Architecture**: `/docs/GENERATION_SERVICE_ARCHITECTURE.md` (this file)

## Testing Coverage

14 unit tests covering:
- ✅ MK1 unlock logic (with/without LECTURE_PDF)
- ✅ MK2 unlock logic (all file combinations)
- ✅ MK3 unlock logic (with/without completed MK2)
- ✅ Generation creation and versioning
- ✅ MK3 previous_content integration
- ✅ Generation history retrieval
- ✅ Response updates and failure handling
- ✅ Latest completed generation fetching

All tests pass (14/14) ✅
