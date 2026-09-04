---
name: docx-comment-reviewer
description: >-
  Extracts Review mode comments from a Word document (.docx), displays them for user approval, then applies the changes — either to a Python generation script that rebuilds the document, or directly to the Word document itself. Trigger phrases: "review comments in my document", "apply Word comments", "check document comments", "update document from comments", "I've added comments to the document".
allowed-tools: execute write_file read_file edit_file grep glob
metadata:
  version: 1.2.0
  tags: word docx comments review document-editing
---

# Word Document Comment Reviewer

Extract Review mode comments from a Word document, display them for user approval, then apply the changes directly to the Word document. If the user explicitly mentions a Python generation script, apply changes to that script instead.

## Language

Always use **American English** spelling when generating or inserting any text into documents. Examples:
- authorization (not authorisation)
- color (not colour)
- organize (not organise)
- center (not centre)
- behavior (not behaviour)

## Trigger

Use this skill when the user says any of:
- "review comments in my document"
- "apply Word comments"
- "check document comments"
- "update document from comments"
- "review my Word comments"
- "I've added comments to the document"
- or any similar request to read and apply Review mode comments from a .docx file

---

## Workflow

### Step 1 — Get the document path

Ask the user: "Please provide the full path to your Word document (.docx)."

Wait for their response before proceeding.

---

### Step 2 — Extract the comments

Read the extraction script from `/skills/docx-comment-reviewer/scripts/extract_comments.py`.

Write its contents to the scratch directory as `extract_comments.py`, then execute:

```
python3 "<scratch_path>/extract_comments.py" "<docx_path>"
```

**If the output contains "NO_COMMENTS":** Tell the user no comments were found and suggest they:
1. Confirm comments are visible in Word under Review → Show Markup → Comments
2. Save the file (⌘S on macOS / Ctrl+S on Windows) and try again

**If the output contains "ERROR":** Report the error message clearly and stop.

**If comments are found:** Continue to Step 3.

---

### Step 3 — Display and seek approval

Display all extracted comments as a rendered table with columns: **#**, **Anchored To**, **Author**, **Comment**.

Then ask: "I found [N] comment(s) above. Ready to apply all of them? Reply **yes** to proceed, or tell me which numbers to skip."

Wait for the user's response. Do not apply any changes yet.

If the user asks to skip specific comments (e.g. "skip #2 and #4"), note which to apply and which to skip before continuing.

**After the user confirms:** proceed directly to Step 4. Do not ask how to apply the changes.

> **Exception:** If the user mentions they have a Python script that generates the document, proceed to Step 4A instead.

---

### Step 4 — Apply changes directly to the Word document

For each approved comment, fully interpret the intent of the requested change. Write a targeted python-docx script to the scratch directory that:

- Opens the .docx file
- Locates the relevant paragraph(s) using the anchored text
- **Handles run-split text:** Word often splits a phrase across multiple runs. Always check `para.text` (the full joined text) first to detect the match, then iterate `para.runs` to find and fix the specific run(s) containing the target text — do not rely on a single-run text match alone
- Makes the change — text replacement, rewrite, insertion, deletion, or formatting adjustment
- For complex comments (rewrites, new paragraphs, structural changes): interprets and applies them fully — do not flag these for manual attention
- Uses American English spelling for any generated or inserted text (see Language section above)
- Saves the document back to the same path

Execute the script. Verify success. Fix any errors before moving to the next comment.

Then proceed to Step 5.

---

### Step 4A — Apply changes to a generation script (only if user has one)

Ask for the full path to the generation script.

For each approved comment:

1. Use `grep` to search for the anchored text in the generation script
2. Use `read_file` to read ±10 lines of surrounding context
3. Use `edit_file` to apply the change described in the comment
4. If the anchored text cannot be found, flag this comment and continue with the others

After all edits are applied, re-run the generation script to rebuild the document:

```
cd "<working_directory>" && python3 "<script_path>"
```

If the script errors, diagnose and fix before proceeding.

Then proceed to Step 5.

---

### Step 5 — Report back

Provide a summary table of every comment processed:

| # | Anchored To | Status | Change Made |
|---|---|---|---|
| 0 | "..." | Applied | Brief description of what changed |
| 1 | "..." | Skipped | User requested skip |

Flag any comment that could not be applied automatically, explain why, and ask the user how to proceed.

---

## Error Handling

| Situation | Action |
|---|---|
| No `comments.xml` in the docx | Tell the user the file has no saved comments. Ask them to save in Word and try again. |
| Anchored text not found in generation script | Mark as "not automatically applied", report it in Step 5, ask user how to handle |
| Script execution error after regeneration | Show error, diagnose, fix the script, re-run |
| python-docx not installed | Run `pip3 install --only-binary :all: python-docx` before proceeding |
| Partial approval | Only apply approved comments. List skipped ones in the Step 5 report with status "Skipped" |
| File not found / bad zip | Report the error clearly and ask the user to verify the path |