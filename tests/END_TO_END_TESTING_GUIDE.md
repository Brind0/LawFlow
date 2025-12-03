# LawFlow End-to-End Testing Guide

**Version:** 1.0
**Date:** December 3, 2025
**Purpose:** Comprehensive manual testing guide for the complete generation workflow

---

## Table of Contents

1. [Pre-Testing Setup](#1-pre-testing-setup)
2. [Test Cases](#2-test-cases)
3. [Visual Verification](#3-visual-verification)
4. [Data Verification](#4-data-verification)
5. [Troubleshooting](#5-troubleshooting)
6. [Test Results Template](#6-test-results-template)

---

## 1. Pre-Testing Setup

### 1.1 Environment Setup

**Prerequisites:**
- [ ] Python 3.9+ installed
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] Streamlit installed: `pip install streamlit`

**Verification:**
```bash
python --version  # Should show 3.9+
streamlit --version  # Should show Streamlit version
pip list | grep "streamlit\|google-api-python-client\|notion-client"
```

---

### 1.2 Configuration Files

#### 1.2.1 Environment Variables (.env file)

Create or verify `.env` file in project root:

```env
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEBUG=false
```

**Checklist:**
- [ ] `.env` file exists in `/Users/charliebrind/Documents/university/LawFlow/`
- [ ] `NOTION_TOKEN` is set (starts with `secret_`)
- [ ] `NOTION_DATABASE_ID` is set (32 character string)

**How to get these values:**
- **Notion Token:** https://www.notion.so/my-integrations
- **Notion Database ID:** From the database URL after `notion.so/` and before `?v=`

---

#### 1.2.2 Google Drive Credentials

**Location:** `/Users/charliebrind/Documents/university/LawFlow/data/credentials/`

**Checklist:**
- [ ] `google_credentials.json` exists in credentials directory
- [ ] File is valid JSON (download from Google Cloud Console)
- [ ] On first run, OAuth flow will create `token.pickle`
- [ ] After first auth, `token.pickle` exists and is valid

**How to get credentials:**
1. Go to Google Cloud Console
2. Enable Google Drive API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download JSON and rename to `google_credentials.json`

---

### 1.3 Database Initialization

**Initialize the database:**
```bash
cd /Users/charliebrind/Documents/university/LawFlow
python scripts/seed_data.py
```

**Expected output:**
```
Database seeded successfully!
Created X modules
Created Y topics
```

**Verification:**
```bash
sqlite3 data/lawflow.db "SELECT COUNT(*) FROM modules;"
sqlite3 data/lawflow.db "SELECT COUNT(*) FROM topics;"
```

**Checklist:**
- [ ] Database file exists: `data/lawflow.db`
- [ ] Modules table has records (should be 8 law modules)
- [ ] Topics table has records (should be multiple topics per module)

---

### 1.4 Test Data Preparation

Create test files for uploading:

**Required test files:**

1. **LECTURE_PDF**: Create or use existing lecture slide PDF
   - [ ] File: `test_lecture.pdf` (any PDF, 1-5 pages)
   - [ ] File size: < 10MB recommended

2. **SOURCE_MATERIAL**: Create or use case law/statute PDF
   - [ ] File: `test_source.pdf` (any PDF)
   - [ ] File size: < 10MB recommended

3. **TUTORIAL_PDF**: Create or use tutorial question PDF
   - [ ] File: `test_tutorial.pdf` (any PDF)
   - [ ] File size: < 10MB recommended

4. **TRANSCRIPT**: Create or use transcript text file
   - [ ] File: `test_transcript.txt` (any text file)
   - [ ] Content: Any text, 1-2 pages recommended

**Note:** For testing purposes, these can be dummy PDFs with placeholder content. The system tests the workflow, not content quality.

---

### 1.5 Notion Database Setup

**Database schema requirements:**

The Notion database should have these properties:
- [ ] **Title** (Title property)
- [ ] **Topic** (Text property)
- [ ] **Stage** (Select property with options: MK1, MK2, MK3)
- [ ] **Version** (Number property)
- [ ] **Status** (Select property with options: Current, Archived)

**How to set up:**
1. Create a new database in Notion
2. Add the properties listed above
3. Share the database with your integration
4. Copy the database ID to `.env`

---

### 1.6 Claude Projects Setup

For the human-in-the-loop workflow, you need Claude Projects:

**Setup:**
- [ ] Create a Claude Project for each law module (e.g., "Land Law", "Tort Law")
- [ ] Each project should be ready to accept uploaded files
- [ ] Have Claude.ai open in a browser tab for testing

**Note:** Files must be uploaded to the correct Claude Project before running the generation workflow.

---

### 1.7 Start the Application

```bash
cd /Users/charliebrind/Documents/university/LawFlow
streamlit run app.py
```

**Expected behavior:**
- [ ] Browser opens to `http://localhost:8501`
- [ ] LawFlow dashboard loads
- [ ] Sidebar shows list of modules
- [ ] No errors in terminal or browser console

**If Google Drive authentication is needed:**
- [ ] OAuth flow opens in browser
- [ ] Grant permissions to the app
- [ ] Redirected back to localhost
- [ ] Token saved to `data/credentials/token.pickle`

---

## 2. Test Cases

### Test Case 1: MK-1 Generation (Foundation)

**Objective:** Verify the complete workflow from lecture PDF upload to Notion page creation.

**Prerequisites:**
- [ ] Application running
- [ ] Database seeded
- [ ] Test lecture PDF ready (`test_lecture.pdf`)

---

#### Step 1.1: Navigate to Topic

1. [ ] Open LawFlow at `http://localhost:8501`
2. [ ] In sidebar, click a module (e.g., "Land Law")
3. [ ] Click a topic (e.g., "Easements")
4. [ ] Topic page loads successfully

**Expected result:** Topic page displays with three stage cards (MK-1, MK-2, MK-3)

---

#### Step 1.2: Verify Initial State

**Check MK-1 card:**
- [ ] Shows 🔒 icon (locked)
- [ ] Description: "Initial lecture summary and extraction"
- [ ] Requirements section shows:
  - [ ] ✗ Lecture PDF
- [ ] Missing section shows: "Lecture PDF"
- [ ] Generate button is disabled

**Check MK-2 card:**
- [ ] Shows 🔒 icon (locked)
- [ ] Requirements section shows:
  - [ ] ✗ Lecture PDF
  - [ ] ✗ Source Material
  - [ ] ✗ Tutorial PDF

**Check MK-3 card:**
- [ ] Shows 🔒 icon (locked)
- [ ] Requirements section shows:
  - [ ] ✗ Lecture PDF
  - [ ] ✗ Source Material
  - [ ] ✗ Tutorial PDF
  - [ ] ✗ Transcript
  - [ ] ✗ MK-2 completed

---

#### Step 1.3: Upload Lecture PDF

1. [ ] Scroll to "Content Vault" section
2. [ ] Click "Upload Content" or file uploader
3. [ ] Select `test_lecture.pdf`
4. [ ] File uploads successfully

**Expected result:**
- [ ] Success message displayed
- [ ] File appears in Content Vault list
- [ ] File name shown: `test_lecture.pdf`
- [ ] Content type: `LECTURE_PDF`
- [ ] Google Drive URL is clickable
- [ ] Page refreshes automatically

---

#### Step 1.4: Verify MK-1 Unlocked

**Check MK-1 card (after upload):**
- [ ] Shows ✅ icon (ready)
- [ ] Requirements section shows:
  - [ ] ✓ Lecture PDF
- [ ] Success message: "✅ Ready to generate!"
- [ ] Generate button is enabled (blue/primary color)

**Check MK-2 and MK-3:**
- [ ] Still locked (requirements partially met)

---

#### Step 1.5: Upload Files to Claude Project

**Before generating, prepare Claude Project:**
1. [ ] Open Claude.ai
2. [ ] Navigate to the correct project (e.g., "Land Law")
3. [ ] Click "Add content" or file upload
4. [ ] Upload `test_lecture.pdf` to the project
5. [ ] Verify file appears in project knowledge base

**Note:** This is CRITICAL - the prompt references these files!

---

#### Step 1.6: Start MK-1 Generation

1. [ ] Click "Generate" button on MK-1 card
2. [ ] Generation modal opens

**Expected modal state:**
- [ ] Title: "Generate MK-1 Foundation"
- [ ] Step 1 visible: Claude file checklist
- [ ] Checkbox for `test_lecture.pdf`
- [ ] Module name shown (e.g., "Land Law")

---

#### Step 1.7: Complete File Checklist (Step 1)

1. [ ] Check the checkbox for `test_lecture.pdf`
2. [ ] All files confirmed

**Expected result:**
- [ ] Step 2 becomes visible
- [ ] Divider appears between steps

---

#### Step 1.8: Copy Prompt (Step 2)

1. [ ] Step 2 header: "Copy Prompt to Claude"
2. [ ] Info message shows module name
3. [ ] Expandable section: "📄 View Full Prompt"
4. [ ] Click expander to view full prompt

**Verify prompt content:**
- [ ] Prompt includes topic name
- [ ] Prompt includes module name
- [ ] Prompt mentions uploaded files
- [ ] Prompt includes MK-1 instructions
- [ ] Prompt is properly formatted

5. [ ] Click "📋 Copy Prompt to Clipboard" button

**Expected result:**
- [ ] Button shows feedback: "✓ Copied!" (for 2 seconds)
- [ ] Prompt is copied to clipboard
- [ ] Step 3 becomes visible

---

#### Step 1.9: Paste Prompt into Claude

1. [ ] Switch to Claude.ai browser tab
2. [ ] Ensure you're in the correct project
3. [ ] Paste the prompt into chat
4. [ ] Press Enter/Send
5. [ ] Wait for Claude to generate response (30-60 seconds)

**Expected result:**
- [ ] Claude processes the uploaded PDF
- [ ] Claude generates structured markdown response
- [ ] Response includes headings, lists, and content
- [ ] Response is complete (not truncated)

---

#### Step 1.10: Copy Claude's Response

1. [ ] Select ALL of Claude's response text
2. [ ] Copy to clipboard (Cmd+C / Ctrl+C)

**Note:** Make sure to copy the ENTIRE response, including all markdown formatting.

---

#### Step 1.11: Paste Response (Step 3)

1. [ ] Switch back to LawFlow browser tab
2. [ ] Step 3 header: "Paste Claude's Response"
3. [ ] Instructions are clear
4. [ ] Large text area is visible
5. [ ] Paste Claude's response into text area

**Expected result:**
- [ ] Text appears in the text area
- [ ] Submit button becomes enabled
- [ ] Warning message disappears

---

#### Step 1.12: Submit Response

1. [ ] Click "Process & Save to Notion" button (blue/primary)
2. [ ] Loading spinner appears: "Processing response and saving to Notion & Drive..."

**Expected behavior during processing:**
- [ ] Loading spinner is visible
- [ ] Button is disabled during processing
- [ ] Process takes 5-15 seconds

**Expected result (success):**
- [ ] Success banner appears: "✅ Generation Complete!"
- [ ] Success checklist shows:
  - [ ] ✓ Converted to Notion blocks
  - [ ] ✓ Created as Notion page
  - [ ] ✓ Backed up to Google Drive
- [ ] Two columns appear with links:
  - [ ] Left: "📝 View in Notion" (clickable link)
  - [ ] Right: "📁 View in Drive" (clickable link)
- [ ] "Close & Refresh" button appears

---

#### Step 1.13: Verify Notion Page

1. [ ] Click "📝 View in Notion" link
2. [ ] Notion page opens in new tab

**Verify Notion page:**
- [ ] Page exists in the correct database
- [ ] Title format: "{Module} - {Topic} - MK1"
- [ ] Properties are set:
  - [ ] Topic: Correct topic name
  - [ ] Stage: "MK1"
  - [ ] Version: 1
  - [ ] Status: "Current"
- [ ] Page content is formatted:
  - [ ] Headings are rendered as Notion heading blocks
  - [ ] Paragraphs are rendered as paragraph blocks
  - [ ] Lists are rendered as bulleted/numbered lists
  - [ ] No raw markdown syntax visible (e.g., no `##` or `**`)
- [ ] Content matches Claude's response
- [ ] No blocks are truncated or missing

---

#### Step 1.14: Verify Drive Backup

1. [ ] Click "📁 View in Drive" link (or navigate to Drive manually)
2. [ ] Navigate to: `LawFlow/{Module}/{Topic}/`

**Verify Drive file:**
- [ ] Folder structure exists: `LawFlow > Land Law > Easements`
- [ ] File exists: `MK1_v1.md`
- [ ] File is markdown format
- [ ] Open file and verify:
  - [ ] Content matches Claude's response
  - [ ] Markdown formatting is preserved
  - [ ] File is complete (not truncated)

---

#### Step 1.15: Close Modal and Verify State

1. [ ] Click "Close & Refresh" button in modal
2. [ ] Page refreshes

**Verify MK-1 card (after generation):**
- [ ] Shows ✨ icon (generated)
- [ ] Description: "Initial lecture summary and extraction"
- [ ] Latest version: "v1"
- [ ] Created timestamp shows (e.g., "Created 2 minutes ago")
- [ ] Two link buttons:
  - [ ] "📝 Notion" (clickable)
  - [ ] "📁 Drive" (clickable)
- [ ] Button changed to: "Regenerate v2"
- [ ] Button is blue/primary (enabled)

**Verify database record:**
```bash
sqlite3 data/lawflow.db "SELECT * FROM generations WHERE stage='MK1';"
```

**Expected database record:**
- [ ] Record exists
- [ ] `topic_id` matches current topic
- [ ] `stage` = "MK1"
- [ ] `version` = 1
- [ ] `status` = "COMPLETED"
- [ ] `prompt_used` contains the generated prompt
- [ ] `response_content` contains Claude's response
- [ ] `notion_page_id` is set
- [ ] `notion_url` is set
- [ ] `drive_backup_id` is set
- [ ] `drive_backup_url` is set
- [ ] `created_at` timestamp is recent

---

#### Test Case 1: Result

**Status:** [ ] PASS [ ] FAIL

**Notes:**
```
[Record any issues, unexpected behavior, or observations here]
```

**Screenshots:** (Optional - attach or reference)
- [ ] MK-1 card before upload
- [ ] MK-1 card after upload (ready state)
- [ ] Generation modal steps
- [ ] Success state
- [ ] Notion page
- [ ] MK-1 card after generation (generated state)

---

---

### Test Case 2: MK-2 Generation (Tutorial Prep)

**Objective:** Verify stage unlock logic and multi-file requirements for MK-2.

**Prerequisites:**
- [ ] Test Case 1 completed (MK-1 generated)
- [ ] Test source material PDF ready (`test_source.pdf`)
- [ ] Test tutorial PDF ready (`test_tutorial.pdf`)

---

#### Step 2.1: Verify MK-2 Initially Locked

**Check MK-2 card (before additional uploads):**
- [ ] Shows 🔒 icon (locked)
- [ ] Requirements section shows:
  - [ ] ✓ Lecture PDF (already uploaded)
  - [ ] ✗ Source Material
  - [ ] ✗ Tutorial PDF
- [ ] Missing section shows:
  - [ ] "Source Material"
  - [ ] "Tutorial PDF"
- [ ] Generate button is disabled

---

#### Step 2.2: Upload Source Material

1. [ ] Scroll to Content Vault
2. [ ] Upload `test_source.pdf`
3. [ ] File uploads successfully

**Expected result:**
- [ ] File appears in Content Vault
- [ ] Content type: `SOURCE_MATERIAL`
- [ ] Drive URL is clickable

**Check MK-2 card:**
- [ ] Still 🔒 (locked) - missing tutorial PDF
- [ ] Requirements updated:
  - [ ] ✓ Lecture PDF
  - [ ] ✓ Source Material
  - [ ] ✗ Tutorial PDF
- [ ] Missing section shows only: "Tutorial PDF"

---

#### Step 2.3: Upload Tutorial PDF

1. [ ] Upload `test_tutorial.pdf`
2. [ ] File uploads successfully

**Expected result:**
- [ ] File appears in Content Vault
- [ ] Content type: `TUTORIAL_PDF`

---

#### Step 2.4: Verify MK-2 Unlocked

**Check MK-2 card (after all uploads):**
- [ ] Shows ✅ icon (ready)
- [ ] Requirements section shows:
  - [ ] ✓ Lecture PDF
  - [ ] ✓ Source Material
  - [ ] ✓ Tutorial PDF
- [ ] Success message: "✅ Ready to generate!"
- [ ] Generate button is enabled

**Check MK-3 card:**
- [ ] Still 🔒 (locked) - missing transcript and completed MK-2
- [ ] Requirements show:
  - [ ] ✓ Lecture PDF
  - [ ] ✓ Source Material
  - [ ] ✓ Tutorial PDF
  - [ ] ✗ Transcript
  - [ ] ✗ MK-2 completed

---

#### Step 2.5: Upload Files to Claude Project

1. [ ] Open Claude.ai project
2. [ ] Upload `test_source.pdf` to project
3. [ ] Upload `test_tutorial.pdf` to project
4. [ ] Verify all three files now in project:
   - [ ] `test_lecture.pdf`
   - [ ] `test_source.pdf`
   - [ ] `test_tutorial.pdf`

---

#### Step 2.6: Generate MK-2

1. [ ] Click "Generate" button on MK-2 card
2. [ ] Generation modal opens
3. [ ] Complete Step 1: Check all files
   - [ ] `test_lecture.pdf`
   - [ ] `test_source.pdf`
   - [ ] `test_tutorial.pdf`
4. [ ] Complete Step 2: Copy prompt

**Verify MK-2 prompt content:**
- [ ] Prompt references all three files
- [ ] Prompt includes MK-2 instructions (detailed analysis)
- [ ] Prompt mentions tutorial preparation
- [ ] Prompt is longer/more detailed than MK-1

5. [ ] Paste prompt into Claude
6. [ ] Wait for Claude's response
7. [ ] Complete Step 3: Paste response
8. [ ] Click "Process & Save to Notion"

**Expected result:**
- [ ] Processing completes successfully
- [ ] Success banner shows
- [ ] Notion page created
- [ ] Drive backup created
- [ ] Links are accessible

---

#### Step 2.7: Verify MK-2 Notion Page

1. [ ] Click Notion link

**Verify Notion page:**
- [ ] Title: "{Module} - {Topic} - MK2"
- [ ] Properties:
  - [ ] Stage: "MK2"
  - [ ] Version: 1
- [ ] Content includes detailed analysis
- [ ] Content is more comprehensive than MK-1
- [ ] Formatting is correct

---

#### Step 2.8: Verify MK-2 Drive Backup

1. [ ] Check Drive folder: `LawFlow/{Module}/{Topic}/`

**Verify:**
- [ ] File exists: `MK2_v1.md`
- [ ] Content matches response

---

#### Step 2.9: Verify MK-2 Card State

1. [ ] Close modal and refresh
2. [ ] Check MK-2 card

**Expected state:**
- [ ] Shows ✨ icon (generated)
- [ ] Version: "v1"
- [ ] Notion and Drive links present
- [ ] Button: "Regenerate v2"

---

#### Step 2.10: Verify MK-3 Still Locked

**Check MK-3 card:**
- [ ] Still 🔒 (locked) - missing transcript
- [ ] Requirements show:
  - [ ] ✓ Lecture PDF
  - [ ] ✓ Source Material
  - [ ] ✓ Tutorial PDF
  - [ ] ✗ Transcript
  - [ ] ✓ MK-2 completed (NOW CHECKED!)
- [ ] Missing section shows: "Transcript"

**This verifies that MK-3 requires BOTH files AND completed MK-2!**

---

#### Test Case 2: Result

**Status:** [ ] PASS [ ] FAIL

**Notes:**
```
[Record any issues, unexpected behavior, or observations here]
```

---

---

### Test Case 3: MK-3 Generation (Exam Revision)

**Objective:** Verify MK-3 includes MK-2 content in prompt and creates comprehensive page.

**Prerequisites:**
- [ ] Test Case 2 completed (MK-2 generated)
- [ ] Test transcript ready (`test_transcript.txt`)

---

#### Step 3.1: Verify MK-3 Initial State

**Before transcript upload:**
- [ ] MK-3 card shows 🔒 (locked)
- [ ] Requirements:
  - [ ] ✓ Lecture PDF
  - [ ] ✓ Source Material
  - [ ] ✓ Tutorial PDF
  - [ ] ✗ Transcript
  - [ ] ✓ MK-2 completed
- [ ] Missing: "Transcript"

---

#### Step 3.2: Upload Transcript

1. [ ] Upload `test_transcript.txt`
2. [ ] File uploads successfully

**Expected result:**
- [ ] File appears in Content Vault
- [ ] Content type: `TRANSCRIPT`

---

#### Step 3.3: Verify MK-3 Unlocked

**Check MK-3 card (after transcript upload):**
- [ ] Shows ✅ icon (ready)
- [ ] Requirements section - ALL checked:
  - [ ] ✓ Lecture PDF
  - [ ] ✓ Source Material
  - [ ] ✓ Tutorial PDF
  - [ ] ✓ Transcript
  - [ ] ✓ MK-2 completed
- [ ] Success message: "✅ Ready to generate!"
- [ ] Generate button is enabled

---

#### Step 3.4: Upload Files to Claude Project

1. [ ] Open Claude.ai project
2. [ ] Upload `test_transcript.txt` to project
3. [ ] Verify all four files now in project:
   - [ ] `test_lecture.pdf`
   - [ ] `test_source.pdf`
   - [ ] `test_tutorial.pdf`
   - [ ] `test_transcript.txt`

---

#### Step 3.5: Generate MK-3

1. [ ] Click "Generate" button on MK-3 card
2. [ ] Generation modal opens
3. [ ] Complete Step 1: Check all files (4 files)
4. [ ] Complete Step 2: Copy prompt

**CRITICAL VERIFICATION - MK-3 Prompt Content:**

**Verify the prompt includes MK-2 content:**
- [ ] Prompt is significantly longer than MK-1 or MK-2
- [ ] Prompt includes a section like "Previous MK-2 Content:" or "## Context from MK-2"
- [ ] Prompt contains the FULL MK-2 response content
- [ ] Prompt references all four uploaded files
- [ ] Prompt includes MK-3 instructions (exam prep, questions)

**This is THE critical feature of MK-3 - it must include MK-2!**

5. [ ] Paste prompt into Claude
6. [ ] Wait for Claude's response (may take longer due to more context)
7. [ ] Complete Step 3: Paste response
8. [ ] Click "Process & Save to Notion"

**Expected result:**
- [ ] Processing completes successfully
- [ ] Success banner shows
- [ ] Notion page created
- [ ] Drive backup created

---

#### Step 3.6: Verify MK-3 Notion Page

1. [ ] Click Notion link

**Verify Notion page is COMPREHENSIVE:**
- [ ] Title: "{Module} - {Topic} - MK3"
- [ ] Properties:
  - [ ] Stage: "MK3"
  - [ ] Version: 1
- [ ] Content is most comprehensive of all stages
- [ ] Content includes exam-focused material
- [ ] Content builds upon MK-2 information
- [ ] Formatting is correct

---

#### Step 3.7: Verify All Three Stages Generated

**Visual verification - all three cards:**

**MK-1 card:**
- [ ] ✨ Generated (blue)
- [ ] v1 shown
- [ ] Links present

**MK-2 card:**
- [ ] ✨ Generated (blue)
- [ ] v1 shown
- [ ] Links present

**MK-3 card:**
- [ ] ✨ Generated (blue)
- [ ] v1 shown
- [ ] Links present

**This represents a COMPLETE topic workflow!**

---

#### Step 3.8: Verify Generation Lineage

**Check database to verify MK-3 references MK-2:**

```bash
sqlite3 data/lawflow.db "SELECT id, stage, version, previous_generation_id FROM generations WHERE stage='MK3';"
```

**Expected result:**
- [ ] `previous_generation_id` is NOT NULL
- [ ] `previous_generation_id` matches MK-2's generation ID

**Verify:**
```bash
sqlite3 data/lawflow.db "SELECT id FROM generations WHERE stage='MK2';"
```
- [ ] The ID matches MK-3's `previous_generation_id`

**This verifies the generation lineage is tracked correctly!**

---

#### Test Case 3: Result

**Status:** [ ] PASS [ ] FAIL

**Notes:**
```
[Record any issues, unexpected behavior, or observations here]
```

**Critical Verification:**
- [ ] MK-3 prompt included full MK-2 content
- [ ] Generation lineage is tracked in database

---

---

### Test Case 4: Regeneration

**Objective:** Verify version increment and new Notion page creation.

**Prerequisites:**
- [ ] Any stage has been generated (v1 exists)

---

#### Step 4.1: Verify Current State

**Select any generated stage card (e.g., MK-1):**
- [ ] Card shows ✨ (generated)
- [ ] Shows "Latest: v1"
- [ ] Button shows "Regenerate v2"

---

#### Step 4.2: Click Regenerate

1. [ ] Click "Regenerate v2" button
2. [ ] Generation modal opens

**Verify modal state:**
- [ ] Title is same as original generation
- [ ] Steps are the same
- [ ] File checklist shows same files

---

#### Step 4.3: Complete Regeneration

1. [ ] Complete all three steps (checklist, copy, paste)
2. [ ] Use a DIFFERENT response from Claude (or modify it)
3. [ ] Submit response

**Expected result:**
- [ ] Processing completes successfully
- [ ] New Notion page created
- [ ] New Drive file created

---

#### Step 4.4: Verify Version Increment

**Check the stage card:**
- [ ] Shows "Latest: v2"
- [ ] Button now shows "Regenerate v3"
- [ ] Links point to NEW Notion page and Drive file

---

#### Step 4.5: Verify Old Version Still Accessible

1. [ ] Expand "📜 View history" on the card

**Expected state:**
- [ ] Shows "2 versions"
- [ ] History expander contains:
  - [ ] v1 entry with date and links
  - [ ] v2 entry with date and links
- [ ] Both versions have working links
- [ ] Oldest version shown first in history

---

#### Step 4.6: Verify Both Notion Pages Exist

1. [ ] Open v1 Notion link (from history)
2. [ ] Open v2 Notion link (from main card)

**Verify:**
- [ ] Both pages exist in Notion database
- [ ] Both have correct version properties (v1 and v2)
- [ ] Content is different between versions
- [ ] Both pages are accessible

---

#### Step 4.7: Verify Both Drive Files Exist

1. [ ] Navigate to Drive folder: `LawFlow/{Module}/{Topic}/`

**Verify:**
- [ ] Two files exist:
  - [ ] `MK1_v1.md` (original)
  - [ ] `MK1_v2.md` (regenerated)
- [ ] Both files are accessible
- [ ] Content differs between versions

---

#### Step 4.8: Verify Database Records

```bash
sqlite3 data/lawflow.db "SELECT id, version, status, notion_url FROM generations WHERE stage='MK1' ORDER BY version;"
```

**Expected result:**
- [ ] Two records returned
- [ ] First record: version=1, status=COMPLETED, notion_url set
- [ ] Second record: version=2, status=COMPLETED, notion_url set
- [ ] Different `notion_url` values
- [ ] Different `drive_backup_url` values

---

#### Test Case 4: Result

**Status:** [ ] PASS [ ] FAIL

**Notes:**
```
[Record any issues, unexpected behavior, or observations here]
```

---

---

### Test Case 5: Stage Lock Logic

**Objective:** Verify requirements enforcement and error messages.

**Prerequisites:**
- [ ] Create a NEW topic (or use a fresh topic with no uploads)

---

#### Step 5.1: Fresh Topic State

**Navigate to a new topic:**
1. [ ] Select module in sidebar
2. [ ] Click "New Topic" or select existing topic with no content
3. [ ] Topic page loads

**Verify all stages locked:**
- [ ] MK-1: 🔒 Locked
- [ ] MK-2: 🔒 Locked
- [ ] MK-3: 🔒 Locked
- [ ] All Generate buttons disabled

---

#### Step 5.2: Upload Only Lecture PDF

1. [ ] Upload a single PDF
2. [ ] System detects as `LECTURE_PDF`

**Verify MK-1 unlocks:**
- [ ] MK-1: ✅ Ready (unlocked)
- [ ] Generate button enabled

**Verify MK-2 and MK-3 remain locked:**
- [ ] MK-2: 🔒 Locked
  - [ ] Requirements show: ✓ Lecture PDF, ✗ Source Material, ✗ Tutorial PDF
  - [ ] Missing: "Source Material", "Tutorial PDF"
- [ ] MK-3: 🔒 Locked
  - [ ] Requirements show: ✓ Lecture PDF, ✗ others
  - [ ] Missing: "Source Material", "Tutorial PDF", "Transcript", "MK-2 completed"

---

#### Step 5.3: Verify Clear Error Messages

**Check MK-2 missing requirements:**
- [ ] Message is clear: "Missing Source Material"
- [ ] Message is clear: "Missing Tutorial PDF"
- [ ] No technical jargon (no "CONTENT_TYPE_ENUM" or similar)
- [ ] Format is consistent

**Check MK-3 missing requirements:**
- [ ] All missing items listed
- [ ] "Missing completed MK2 generation" is shown
- [ ] Messages are user-friendly

---

#### Step 5.4: Test Partial Upload

1. [ ] Upload source material (but NOT tutorial PDF)
2. [ ] Page refreshes

**Verify MK-2 STILL locked:**
- [ ] MK-2: 🔒 Locked (not ✅ Ready)
- [ ] Requirements: ✓ Lecture PDF, ✓ Source Material, ✗ Tutorial PDF
- [ ] Missing: "Tutorial PDF" only
- [ ] Generate button still disabled

**This verifies ALL requirements must be met!**

---

#### Step 5.5: Complete MK-1 but Not MK-2

1. [ ] Generate and complete MK-1
2. [ ] Do NOT upload tutorial PDF (MK-2 incomplete)
3. [ ] Upload transcript

**Verify MK-3 STILL locked:**
- [ ] MK-3: 🔒 Locked
- [ ] Requirements show:
  - [ ] ✓ Lecture PDF
  - [ ] ✓ Source Material
  - [ ] ✗ Tutorial PDF
  - [ ] ✓ Transcript
  - [ ] ✗ MK-2 completed (IMPORTANT!)
- [ ] Generate button disabled

**This verifies MK-3 requires BOTH files AND completed MK-2!**

---

#### Test Case 5: Result

**Status:** [ ] PASS [ ] FAIL

**Notes:**
```
[Record any issues, unexpected behavior, or observations here]
```

**Critical Verification:**
- [ ] Requirements are strictly enforced
- [ ] Error messages are user-friendly
- [ ] MK-3 requires completed MK-2 (not just files)

---

---

### Test Case 6: Error Handling

**Objective:** Verify graceful error handling and helpful error messages.

**Prerequisites:**
- [ ] Topic with uploaded files
- [ ] Ability to modify configuration

---

#### Step 6.1: Invalid Notion Token

**Setup:**
1. [ ] Edit `.env` file
2. [ ] Change `NOTION_TOKEN` to invalid value (e.g., `secret_invalid`)
3. [ ] Save file
4. [ ] Restart Streamlit app

**Test:**
1. [ ] Navigate to topic
2. [ ] Start generation workflow
3. [ ] Complete steps 1-2 (files, prompt)
4. [ ] Paste response
5. [ ] Click "Process & Save to Notion"

**Expected behavior:**
- [ ] Error message appears (not success)
- [ ] Error message is clear and actionable
- [ ] Error mentions: "Check your Notion token"
- [ ] Error includes troubleshooting section
- [ ] Pasted response is NOT lost (still in text area)
- [ ] User can fix and retry

**Verify system doesn't crash:**
- [ ] App continues running
- [ ] Can navigate to other pages
- [ ] No stack traces visible to user

**Cleanup:**
1. [ ] Restore correct `NOTION_TOKEN` in `.env`
2. [ ] Restart app

---

#### Step 6.2: Missing Drive Credentials

**Setup:**
1. [ ] Temporarily rename `google_credentials.json` to `google_credentials.json.bak`
2. [ ] Restart Streamlit app

**Test:**
1. [ ] Start generation workflow
2. [ ] Try to process response

**Expected behavior:**
- [ ] Error message about Drive credentials
- [ ] Message mentions: "Ensure your Google Drive credentials are configured"
- [ ] Helpful instructions provided

**Cleanup:**
1. [ ] Rename file back to `google_credentials.json`
2. [ ] Restart app

---

#### Step 6.3: Invalid Notion Database ID

**Setup:**
1. [ ] Edit `.env` file
2. [ ] Change `NOTION_DATABASE_ID` to invalid value
3. [ ] Save and restart

**Test:**
1. [ ] Try to process response

**Expected behavior:**
- [ ] Error about database ID
- [ ] Message mentions: "Verify the Notion database ID is correct"

**Cleanup:**
1. [ ] Restore correct database ID

---

#### Step 6.4: Network Failure Simulation

**Test (if possible):**
1. [ ] Disconnect from internet
2. [ ] Try to process response

**Expected behavior:**
- [ ] Error about connectivity
- [ ] Message mentions: "Check your internet connection"

---

#### Test Case 6: Result

**Status:** [ ] PASS [ ] FAIL

**Notes:**
```
[Record any issues, unexpected behavior, or observations here]
```

**Critical Verification:**
- [ ] No crashes or stack traces visible
- [ ] Error messages are helpful and actionable
- [ ] User can recover and retry
- [ ] Pasted content is not lost on error

---

---

### Test Case 7: Clipboard Functionality

**Objective:** Verify clipboard component works across browsers.

**Prerequisites:**
- [ ] Topic with uploaded files ready to generate

---

#### Step 7.1: Test in Chrome

**Setup:**
1. [ ] Open LawFlow in Google Chrome
2. [ ] Navigate to topic
3. [ ] Start generation workflow

**Test Copy Button:**
1. [ ] Click "📋 Copy Prompt to Clipboard"
2. [ ] Observe button feedback

**Expected behavior:**
- [ ] Button shows "✓ Copied!" immediately
- [ ] Green checkmark visible
- [ ] Feedback disappears after 2 seconds
- [ ] No JavaScript errors in console (F12 > Console)

**Test Clipboard Content:**
1. [ ] Open a text editor (VS Code, TextEdit, Notepad)
2. [ ] Paste (Cmd+V / Ctrl+V)

**Verify:**
- [ ] Full prompt text is pasted
- [ ] No truncation
- [ ] Special characters preserved (quotes, backticks, etc.)
- [ ] Line breaks preserved

**Test Paste Area:**
1. [ ] Generate a test response in Claude
2. [ ] Copy Claude's response
3. [ ] Paste into LawFlow text area

**Verify:**
- [ ] Text appears in area
- [ ] Formatting preserved (markdown)
- [ ] No character limit issues
- [ ] Scrollbar appears if content is long

---

#### Step 7.2: Test in Firefox

**Setup:**
1. [ ] Open LawFlow in Mozilla Firefox
2. [ ] Navigate to same topic
3. [ ] Start generation workflow

**Repeat all tests from Step 7.1:**
- [ ] Copy button works
- [ ] Feedback shows correctly
- [ ] Paste works in external editor
- [ ] Paste area works

**Firefox-specific verification:**
- [ ] No permission popups (localhost is trusted)
- [ ] No console errors

---

#### Step 7.3: Test in Safari

**Setup:**
1. [ ] Open LawFlow in Safari (if on macOS)
2. [ ] Navigate to same topic
3. [ ] Start generation workflow

**Repeat all tests from Step 7.1:**
- [ ] Copy button works
- [ ] Feedback shows correctly
- [ ] Paste works in external editor
- [ ] Paste area works

**Safari-specific verification:**
- [ ] Clipboard API supported (Safari 13.1+)
- [ ] No permission issues

---

#### Step 7.4: Test with Large Prompts

**Setup:**
1. [ ] Use MK-3 generation (longest prompt, includes MK-2 content)
2. [ ] Prompt should be > 10KB

**Test:**
1. [ ] Copy MK-3 prompt
2. [ ] Verify copy feedback
3. [ ] Paste into external editor
4. [ ] Check file size or character count

**Verify:**
- [ ] Full prompt copied (not truncated)
- [ ] Size is > 10KB / > 10,000 characters
- [ ] MK-2 content is included in copied text

---

#### Step 7.5: Test Edge Cases

**Test empty clipboard:**
1. [ ] Don't click copy button
2. [ ] Try to paste in text area
3. [ ] Should work (user can manually copy/paste)

**Test multiple copies:**
1. [ ] Click copy button twice
2. [ ] Verify it works both times
3. [ ] No errors or state issues

**Test rapid clicking:**
1. [ ] Click copy button rapidly 5 times
2. [ ] Verify no JavaScript errors
3. [ ] Feedback still shows correctly

---

#### Test Case 7: Result

**Browsers tested:**
- [ ] Chrome - PASS / FAIL
- [ ] Firefox - PASS / FAIL
- [ ] Safari - PASS / FAIL

**Notes:**
```
[Record any browser-specific issues here]
```

**Critical Verification:**
- [ ] Copy button works in all browsers
- [ ] Large prompts (>10KB) copy successfully
- [ ] No truncation or data loss
- [ ] Visual feedback is clear

---

---

## 3. Visual Verification

This section provides a checklist for visual/UI verification.

### 3.1 Stage Card States

**Locked state (🔒):**
- [ ] Gray/neutral color scheme
- [ ] Lock icon (🔒) visible
- [ ] Generate button disabled (grayed out)
- [ ] Requirements section shows ✗ for missing items
- [ ] Missing section lists what's needed
- [ ] Hover text on disabled button explains why

**Ready state (✅):**
- [ ] Green/positive color scheme
- [ ] Checkmark icon (✅) visible
- [ ] Generate button enabled (blue/primary color)
- [ ] Requirements section shows all ✓
- [ ] Success message: "✅ Ready to generate!"
- [ ] Button is prominently styled

**Generated state (✨):**
- [ ] Blue/success color scheme
- [ ] Sparkle icon (✨) visible
- [ ] Shows "Latest: vX" with version number
- [ ] Shows creation timestamp (humanized, e.g., "2 hours ago")
- [ ] Two link buttons: Notion and Drive
- [ ] Regenerate button is enabled
- [ ] History expander appears if multiple versions

---

### 3.2 Content Vault Display

**File list:**
- [ ] Each file shows:
  - [ ] File name
  - [ ] Content type (human-readable, e.g., "Lecture PDF")
  - [ ] Upload timestamp
  - [ ] Drive link (icon or text)
  - [ ] Delete button (trash icon)
- [ ] Files are sorted (newest first or by type)
- [ ] Layout is clean and scannable

**Upload interface:**
- [ ] File uploader is prominent
- [ ] Accepted file types are listed (.pdf, .txt)
- [ ] Upload button is clear
- [ ] Progress indicator during upload

---

### 3.3 Generation Modal

**Modal appearance:**
- [ ] Modal overlays the page
- [ ] Title is clear (e.g., "Generate MK-1 Foundation")
- [ ] Steps are numbered and visually distinct
- [ ] Progressive disclosure (steps appear as previous complete)
- [ ] Dividers between sections

**Step 1 - File checklist:**
- [ ] Module name prominently displayed
- [ ] Each file has a checkbox
- [ ] Clear instruction text
- [ ] Checkboxes are interactive

**Step 2 - Copy prompt:**
- [ ] Info banner with module name
- [ ] Expandable prompt preview
- [ ] Preview shows actual prompt
- [ ] Copy button is prominent
- [ ] Visual feedback on copy ("✓ Copied!")

**Step 3 - Paste response:**
- [ ] Clear instructions (3 numbered steps)
- [ ] Text area is large (400px height)
- [ ] Placeholder text is helpful
- [ ] Submit button below text area
- [ ] Button disabled until text entered
- [ ] Warning caption when disabled

**Success state:**
- [ ] Success banner stands out (green)
- [ ] Checkmarks for each step
- [ ] Links are clearly labeled
- [ ] Close button is prominent

---

### 3.4 Success Feedback

**After generation completes:**
- [ ] Balloons animation plays (optional, check if implemented)
- [ ] Success banner at top of modal
- [ ] Two clickable link columns (Notion | Drive)
- [ ] Links open in new tab
- [ ] "Close & Refresh" button

**After closing modal:**
- [ ] Page refreshes automatically
- [ ] Stage card updates to "generated" state
- [ ] New version number visible
- [ ] Links immediately accessible

---

### 3.5 Responsive Layout

**Desktop (1920x1080):**
- [ ] Three stage cards side-by-side
- [ ] Cards are equal width
- [ ] Content is readable
- [ ] No horizontal scrolling

**Laptop (1440x900):**
- [ ] Layout still works
- [ ] Cards may be slightly narrower
- [ ] Text doesn't wrap awkwardly

**Tablet (if testing):**
- [ ] Cards stack vertically or adjust width
- [ ] All content accessible

---

### Visual Verification Result

**Status:** [ ] PASS [ ] FAIL

**Notes:**
```
[Record any visual issues, layout problems, or styling concerns here]
```

---

---

## 4. Data Verification

This section provides verification steps for backend data integrity.

### 4.1 Database Schema Verification

**Check tables exist:**
```bash
sqlite3 data/lawflow.db ".tables"
```

**Expected tables:**
- [ ] `modules`
- [ ] `topics`
- [ ] `content_items`
- [ ] `generations`

**Check generations table schema:**
```bash
sqlite3 data/lawflow.db ".schema generations"
```

**Expected columns:**
- [ ] `id` (TEXT PRIMARY KEY)
- [ ] `topic_id` (TEXT)
- [ ] `stage` (TEXT)
- [ ] `version` (INTEGER)
- [ ] `status` (TEXT)
- [ ] `prompt_used` (TEXT)
- [ ] `response_content` (TEXT)
- [ ] `notion_page_id` (TEXT)
- [ ] `notion_url` (TEXT)
- [ ] `drive_backup_id` (TEXT)
- [ ] `drive_backup_url` (TEXT)
- [ ] `previous_generation_id` (TEXT)
- [ ] `created_at` (TIMESTAMP)
- [ ] `updated_at` (TIMESTAMP)

---

### 4.2 Content Items Verification

**After uploading files, check content_items table:**
```bash
sqlite3 data/lawflow.db "SELECT file_name, content_type, is_active FROM content_items WHERE topic_id='[TOPIC_ID]';"
```

**Replace `[TOPIC_ID]` with actual topic ID from UI or query:**
```bash
sqlite3 data/lawflow.db "SELECT id, name FROM topics LIMIT 1;"
```

**Verify:**
- [ ] All uploaded files have records
- [ ] `content_type` matches uploaded file type
- [ ] `is_active` is 1 (true) for all
- [ ] `drive_file_id` is set
- [ ] `drive_url` is set

**After deleting a file, check:**
```bash
sqlite3 data/lawflow.db "SELECT file_name, is_active FROM content_items WHERE topic_id='[TOPIC_ID]';"
```

**Verify soft delete:**
- [ ] Deleted file still has record
- [ ] `is_active` is 0 (false)
- [ ] File is not shown in UI

---

### 4.3 Generations Table Verification

**After completing a generation:**
```bash
sqlite3 data/lawflow.db "SELECT stage, version, status, notion_page_id IS NOT NULL as has_notion, drive_backup_id IS NOT NULL as has_drive FROM generations WHERE topic_id='[TOPIC_ID]';"
```

**Verify:**
- [ ] Record exists for each completed generation
- [ ] `status` is "COMPLETED"
- [ ] `has_notion` is 1 (TRUE)
- [ ] `has_drive` is 1 (TRUE)
- [ ] `version` increments correctly (1, 2, 3...)

**Check prompt and response are stored:**
```bash
sqlite3 data/lawflow.db "SELECT LENGTH(prompt_used), LENGTH(response_content) FROM generations WHERE id='[GENERATION_ID]';"
```

**Verify:**
- [ ] `prompt_used` length > 0 (should be 1000-20000+ chars)
- [ ] `response_content` length > 0 (should be 500-10000+ chars)

---

### 4.4 Foreign Key Integrity

**Verify generations link to topics:**
```bash
sqlite3 data/lawflow.db "SELECT g.id, t.name FROM generations g JOIN topics t ON g.topic_id = t.id LIMIT 5;"
```

**Verify:**
- [ ] Query returns results (no orphaned generations)
- [ ] Topic names are correct

**Verify content_items link to topics:**
```bash
sqlite3 data/lawflow.db "SELECT c.file_name, t.name FROM content_items c JOIN topics t ON c.topic_id = t.id LIMIT 5;"
```

**Verify:**
- [ ] Query returns results
- [ ] Topic names are correct

---

### 4.5 Version Numbering

**Check version sequence for a stage:**
```bash
sqlite3 data/lawflow.db "SELECT version, status, created_at FROM generations WHERE topic_id='[TOPIC_ID]' AND stage='MK1' ORDER BY version;"
```

**Verify:**
- [ ] Versions start at 1
- [ ] Versions increment sequentially (1, 2, 3...)
- [ ] No gaps in version numbers
- [ ] Versions are ordered by `created_at`

---

### 4.6 Notion Page IDs

**Verify Notion page IDs are UUIDs:**
```bash
sqlite3 data/lawflow.db "SELECT notion_page_id FROM generations WHERE notion_page_id IS NOT NULL LIMIT 5;"
```

**Verify:**
- [ ] IDs are 32-character strings (with dashes removed)
- [ ] IDs are unique
- [ ] IDs match format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

**Test Notion URL format:**
```bash
sqlite3 data/lawflow.db "SELECT notion_url FROM generations WHERE notion_url IS NOT NULL LIMIT 1;"
```

**Verify:**
- [ ] URL starts with `https://www.notion.so/`
- [ ] URL is accessible (copy-paste into browser)

---

### 4.7 Drive Backup Files

**Verify Drive file IDs:**
```bash
sqlite3 data/lawflow.db "SELECT drive_backup_id, drive_backup_url FROM generations WHERE drive_backup_id IS NOT NULL LIMIT 5;"
```

**Verify:**
- [ ] `drive_backup_id` is set (Google's file ID format)
- [ ] `drive_backup_url` starts with `https://drive.google.com/`
- [ ] URL is accessible

**Check Drive folder structure:**
1. [ ] Open Google Drive
2. [ ] Navigate to `LawFlow/` folder
3. [ ] Check subfolders exist for each module (e.g., `Land Law/`)
4. [ ] Check subfolders exist for each topic (e.g., `Easements/`)
5. [ ] Check markdown files exist in topic folders:
   - [ ] `MK1_v1.md`, `MK1_v2.md`, etc.
   - [ ] `MK2_v1.md`
   - [ ] `MK3_v1.md`

---

### Data Verification Result

**Status:** [ ] PASS [ ] FAIL

**Notes:**
```
[Record any data integrity issues, missing records, or anomalies here]
```

---

---

## 5. Troubleshooting

Common issues and solutions during testing.

---

### 5.1 Application Won't Start

**Symptom:** `streamlit run app.py` fails or shows errors

**Possible causes and solutions:**

1. **Missing dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database file missing**
   ```bash
   python scripts/seed_data.py
   ```

3. **Import errors**
   - Check Python version: `python --version` (should be 3.9+)
   - Check virtual environment is activated

4. **Port already in use**
   - Kill existing Streamlit process
   - Or use different port: `streamlit run app.py --server.port 8502`

---

### 5.2 Clipboard Not Working

**Symptom:** Copy button doesn't copy or shows error

**Possible causes and solutions:**

1. **Not using localhost**
   - Clipboard API requires secure context
   - Solution: Use `http://localhost:8501` (not IP address)

2. **Browser doesn't support Clipboard API**
   - Check browser version:
     - Chrome 66+
     - Firefox 63+
     - Safari 13.1+
   - Solution: Update browser

3. **JavaScript errors in console**
   - Open browser console (F12)
   - Check for errors
   - Verify JavaScript bridge is loaded

4. **Text not escaping correctly**
   - If prompt contains backticks, check escaping in `clipboard.py`
   - Verify template literal escaping

**Workaround:**
- Manually select text in the prompt preview expander
- Copy with Cmd+C / Ctrl+C

---

### 5.3 Notion Errors

**Symptom:** "Failed to process response" with Notion error

**Possible causes and solutions:**

1. **Invalid Notion token**
   - Check `.env` file
   - Token should start with `secret_`
   - Verify token is not expired
   - Solution: Generate new token at https://www.notion.so/my-integrations

2. **Wrong database ID**
   - Verify `NOTION_DATABASE_ID` in `.env`
   - ID is 32 characters (no dashes)
   - Solution: Copy from database URL

3. **Database not shared with integration**
   - Open Notion database
   - Click "..." menu
   - Select "Add connections"
   - Choose your integration
   - Solution: Share database with integration

4. **Rate limiting**
   - Notion API has rate limits (3 requests/second)
   - Symptom: Error after multiple rapid generations
   - Solution: Wait 1-2 seconds between generations

5. **Notion API is down**
   - Check https://status.notion.so/
   - Solution: Wait and retry

---

### 5.4 Google Drive Errors

**Symptom:** "Failed to process response" with Drive error

**Possible causes and solutions:**

1. **Missing credentials file**
   - Check `data/credentials/google_credentials.json` exists
   - Solution: Download from Google Cloud Console

2. **Token expired**
   - Delete `data/credentials/token.pickle`
   - Restart app
   - Re-authenticate via OAuth flow

3. **Insufficient permissions**
   - Verify OAuth scopes include Drive API
   - Solution: Delete token.pickle and re-authenticate

4. **Folder permissions**
   - Check `LawFlow/` folder exists in Drive
   - Verify app has write permissions
   - Solution: Manually create folder or re-authenticate

5. **Network issues**
   - Check internet connection
   - Check firewall settings
   - Solution: Verify connectivity

---

### 5.5 Stage Not Unlocking

**Symptom:** Stage card stays locked despite uploading files

**Possible causes and solutions:**

1. **Wrong content type**
   - Check Content Vault shows correct type (e.g., "Lecture PDF")
   - Solution: Delete and re-upload with correct type

2. **File not active**
   - File may be soft-deleted
   - Check database: `SELECT is_active FROM content_items WHERE file_name='...'`
   - Solution: Re-upload file

3. **Missing MK-2 for MK-3**
   - MK-3 requires COMPLETED MK-2 (not just files)
   - Check MK-2 card shows ✨ (generated)
   - Solution: Complete MK-2 generation first

4. **Cache issue**
   - Streamlit may have stale state
   - Solution: Refresh page (F5) or restart app

---

### 5.6 Generation Stays Pending

**Symptom:** Generation created but never completes

**Possible causes and solutions:**

1. **User didn't complete workflow**
   - Check if modal was closed before submitting
   - Check database: `SELECT status FROM generations WHERE id='...'`
   - Solution: Start new generation (will increment version)

2. **Error during processing**
   - Check terminal for Python errors
   - Check browser console for JavaScript errors
   - Solution: Review error logs and fix issue

3. **Network timeout**
   - Notion or Drive API took too long
   - Solution: Retry generation

---

### 5.7 Notion Page Not Formatting Correctly

**Symptom:** Notion page has raw markdown or broken formatting

**Possible causes and solutions:**

1. **Markdown converter issue**
   - Check response content in database
   - Verify markdown is valid
   - Solution: Regenerate with better-formatted response

2. **Block size limit**
   - Notion blocks have 2000 character limit
   - Large paragraphs may be truncated
   - Check `markdown_converter.py` handles splitting
   - Solution: Verify converter splits large blocks

3. **Unsupported markdown syntax**
   - Notion doesn't support all markdown features
   - Check for complex tables, footnotes, etc.
   - Solution: Simplify markdown or update converter

---

### 5.8 Database Locked Error

**Symptom:** "Database is locked" error in terminal

**Possible causes and solutions:**

1. **Multiple connections**
   - SQLite doesn't handle concurrent writes well
   - Solution: Use context managers (`with get_connection()`)

2. **Long-running query**
   - Previous query didn't close connection
   - Solution: Restart app

3. **Database corruption**
   - Rare but possible
   - Solution: Backup database and repair or recreate

---

### 5.9 Balloons Not Showing

**Symptom:** No balloons animation after successful generation

**Possible causes:**
- This is NOT a critical issue (cosmetic only)
- May not be implemented yet
- Check `generation_modal.py` for `st.balloons()` call

**Solution:**
- Not critical for functionality
- Can add later in UI polish phase

---

### 5.10 Links Not Working

**Symptom:** Notion or Drive links don't open or show 404

**Possible causes and solutions:**

1. **URL not saved**
   - Check database: `SELECT notion_url FROM generations WHERE id='...'`
   - If NULL, generation didn't complete properly
   - Solution: Regenerate

2. **Notion page deleted**
   - User may have deleted page manually
   - Solution: Regenerate

3. **Drive file deleted**
   - File may be in trash
   - Solution: Restore from Drive trash or regenerate

4. **Permissions issue**
   - Notion page not shared
   - Drive file permissions changed
   - Solution: Verify permissions in Notion/Drive

---

## 6. Test Results Template

Use this template to record test results.

---

### Test Session Information

**Date:** _______________
**Tester Name:** _______________
**Environment:**
- OS: _______________
- Python Version: _______________
- Streamlit Version: _______________
- Browser(s): _______________

---

### Test Case Results Summary

| Test Case | Status | Notes |
|-----------|--------|-------|
| TC1: MK-1 Generation | ☐ PASS ☐ FAIL | |
| TC2: MK-2 Generation | ☐ PASS ☐ FAIL | |
| TC3: MK-3 Generation | ☐ PASS ☐ FAIL | |
| TC4: Regeneration | ☐ PASS ☐ FAIL | |
| TC5: Stage Lock Logic | ☐ PASS ☐ FAIL | |
| TC6: Error Handling | ☐ PASS ☐ FAIL | |
| TC7: Clipboard (Chrome) | ☐ PASS ☐ FAIL | |
| TC7: Clipboard (Firefox) | ☐ PASS ☐ FAIL | |
| TC7: Clipboard (Safari) | ☐ PASS ☐ FAIL | |

---

### Detailed Test Case Results

#### Test Case 1: MK-1 Generation

**Status:** ☐ PASS ☐ FAIL

**Steps completed:**
- [ ] Navigate to topic
- [ ] Verify initial locked state
- [ ] Upload lecture PDF
- [ ] Verify MK-1 unlocked
- [ ] Upload files to Claude Project
- [ ] Start generation
- [ ] Complete file checklist
- [ ] Copy prompt
- [ ] Paste prompt into Claude
- [ ] Copy Claude's response
- [ ] Paste response into LawFlow
- [ ] Submit response
- [ ] Verify Notion page created
- [ ] Verify Drive backup created
- [ ] Close modal
- [ ] Verify card state updated

**Issues found:**
```
[Describe any issues, unexpected behavior, or bugs encountered]
```

**Screenshots attached:** ☐ Yes ☐ No

---

#### Test Case 2: MK-2 Generation

**Status:** ☐ PASS ☐ FAIL

**Steps completed:**
- [ ] Verify MK-2 initially locked
- [ ] Upload source material
- [ ] Upload tutorial PDF
- [ ] Verify MK-2 unlocked
- [ ] Complete generation workflow
- [ ] Verify Notion page
- [ ] Verify MK-3 still locked (needs completed MK-2)

**Issues found:**
```
[Describe any issues]
```

---

#### Test Case 3: MK-3 Generation

**Status:** ☐ PASS ☐ FAIL

**Critical verification:**
- [ ] MK-3 prompt included FULL MK-2 content
- [ ] Prompt was significantly longer than MK-1/MK-2
- [ ] Generation lineage tracked in database

**Steps completed:**
- [ ] Upload transcript
- [ ] Verify MK-3 unlocked
- [ ] Complete generation workflow
- [ ] Verify comprehensive Notion page
- [ ] Verify all three stages generated

**Issues found:**
```
[Describe any issues]
```

---

#### Test Case 4: Regeneration

**Status:** ☐ PASS ☐ FAIL

**Steps completed:**
- [ ] Click "Regenerate v2"
- [ ] Complete workflow with different response
- [ ] Verify version incremented to v2
- [ ] Verify history shows both versions
- [ ] Verify both Notion pages exist
- [ ] Verify both Drive files exist

**Issues found:**
```
[Describe any issues]
```

---

#### Test Case 5: Stage Lock Logic

**Status:** ☐ PASS ☐ FAIL

**Steps completed:**
- [ ] Fresh topic - all stages locked
- [ ] Upload only lecture PDF - only MK-1 unlocked
- [ ] Upload partial files - stages remain locked
- [ ] Complete MK-1, no tutorial PDF - MK-3 still locked
- [ ] Verified MK-3 requires completed MK-2

**Issues found:**
```
[Describe any issues]
```

---

#### Test Case 6: Error Handling

**Status:** ☐ PASS ☐ FAIL

**Errors tested:**
- [ ] Invalid Notion token
- [ ] Missing Drive credentials
- [ ] Invalid database ID
- [ ] Network failure (if possible)

**Verification:**
- [ ] No crashes
- [ ] Helpful error messages
- [ ] User can recover
- [ ] Pasted content not lost

**Issues found:**
```
[Describe any issues]
```

---

#### Test Case 7: Clipboard Functionality

**Status:**
- Chrome: ☐ PASS ☐ FAIL
- Firefox: ☐ PASS ☐ FAIL
- Safari: ☐ PASS ☐ FAIL

**Verification:**
- [ ] Copy button works in all browsers
- [ ] Visual feedback appears ("✓ Copied!")
- [ ] Full prompt copied (not truncated)
- [ ] Large prompts work (>10KB)
- [ ] Paste area accepts content
- [ ] Special characters preserved

**Browser-specific issues:**
```
[Describe any browser-specific problems]
```

---

### Visual Verification

**Stage card states:**
- [ ] Locked state (🔒) renders correctly
- [ ] Ready state (✅) renders correctly
- [ ] Generated state (✨) renders correctly

**Content Vault:**
- [ ] Files display correctly
- [ ] Upload interface is clear
- [ ] Delete functionality works

**Generation Modal:**
- [ ] Steps are clearly numbered
- [ ] Progressive disclosure works
- [ ] Success state is prominent
- [ ] Links are clickable

**Responsive layout:**
- [ ] Desktop (1920x1080) - works well
- [ ] Laptop (1440x900) - works well
- [ ] Tablet (if tested) - works well

**Issues found:**
```
[Describe any visual/UI issues]
```

---

### Data Verification

**Database checks:**
- [ ] All tables exist and have correct schema
- [ ] Content items records are correct
- [ ] Generations records are complete
- [ ] Foreign keys are valid
- [ ] Version numbering is sequential
- [ ] Notion page IDs are valid UUIDs
- [ ] Drive backup IDs and URLs are set

**Drive folder structure:**
- [ ] `LawFlow/` folder exists
- [ ] Module subfolders exist
- [ ] Topic subfolders exist
- [ ] Markdown files exist (MK1_v1.md, etc.)

**Notion database:**
- [ ] Pages created with correct properties
- [ ] Content formatted correctly
- [ ] No raw markdown visible

**Issues found:**
```
[Describe any data integrity issues]
```

---

### Overall Test Results

**Overall Status:** ☐ PASS ☐ FAIL

**Pass Criteria:**
- [ ] All critical test cases pass (TC1, TC2, TC3)
- [ ] Stage unlock logic works correctly
- [ ] MK-3 includes MK-2 content in prompt
- [ ] Clipboard works in at least 2 browsers
- [ ] No crashes or data loss
- [ ] Error handling is graceful

**Critical Issues Found:**
```
[List any critical bugs that prevent core functionality]
```

**Non-Critical Issues Found:**
```
[List minor bugs, UX improvements, or polish items]
```

**Recommendations:**
```
[Provide recommendations for next steps, fixes, or improvements]
```

---

### Screenshots and Evidence

**Attach or link to:**
1. [ ] Initial locked state (all three cards)
2. [ ] Ready state (MK-1 after upload)
3. [ ] Generation modal (all three steps)
4. [ ] Success state
5. [ ] Generated state (card after completion)
6. [ ] Notion page example
7. [ ] Drive folder structure
8. [ ] History expander with multiple versions
9. [ ] Error message examples
10. [ ] Database query results

---

### Sign-Off

**Tester Signature:** _______________
**Date:** _______________

**Reviewer Signature:** _______________
**Date:** _______________

---

## End of Test Guide

**For questions or issues during testing, refer to:**
- Project documentation: `/Users/charliebrind/Documents/university/LawFlow/CLAUDE.md`
- Roadmap: `/Users/charliebrind/Documents/university/LawFlow/roadmap.md`
- Architecture docs: `/Users/charliebrind/Documents/university/LawFlow/docs/`

**Good luck with testing!** 🧪
