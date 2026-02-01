# VibeVoice Architecture Diagram

## Overview: Library + Extensions

```
┌─────────────────────────────────────────────────────────────────────┐
│                         vv_context Library                          │
│                    (Reusable AI Coding Logic)                       │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                    Core Interfaces                         │   │
│  │                                                            │   │
│  │  • ILanguageModel    - AI provider abstraction            │   │
│  │  • IFileEditor       - File system abstraction            │   │
│  │  • IContextGatherer  - Context gathering abstraction      │   │
│  │  • IMessage          - Message format                     │   │
│  │  • ProcessingResult  - Result format                      │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                   MessageProcessor                         │   │
│  │                                                            │   │
│  │  • processMessage()        - Main entry point             │   │
│  │  • gatherContext()         - Smart context collection     │   │
│  │  • parseFileEdits()        - Extract edit blocks          │   │
│  │  • extractKeywords()       - Keyword extraction           │   │
│  │  • conversationHistory     - State management             │   │
│  │  • testMode                - Mock responses               │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ imports
                                    │
        ┌───────────────────────────┴──────────────────────────┐
        │                                                       │
        ▼                                                       ▼
┌───────────────────────┐                         ┌───────────────────────┐
│  copilot_extension    │                         │    claude_cli         │
│  (GitHub Copilot)     │                         │    (Future)           │
│                       │                         │                       │
│  Adapters:            │                         │  Adapters:            │
│  ├─ VSCodeLanguageModel│                        │  ├─ ClaudeLanguageModel│
│  │  (Copilot API)     │                         │  │  (Claude API)      │
│  ├─ VSCodeFileEditor  │                         │  ├─ NodeFileEditor    │
│  │  (vscode.workspace.fs)│                      │  │  (fs/promises)     │
│  └─ VSCodeContextGatherer│                      │  └─ NodeContextGatherer│
│     (vscode.workspace) │                         │     (glob + fs)       │
│                       │                         │                       │
│  Extension Features:  │                         │  CLI Features:        │
│  • Chat participant   │                         │  • Command interface  │
│  • WebSocket client   │                         │  • Interactive mode   │
│  • Voice commands     │                         │  • File watching      │
│  • VSCode UI          │                         │  • Session mgmt       │
└───────────────────────┘                         └───────────────────────┘
```

## Data Flow: Voice Command Example

```
┌─────────────┐
│   iOS App   │  "Add error handling to getUserData"
└──────┬──────┘
       │ 1. Record audio
       ▼
┌─────────────┐
│  AWS Polly  │  Generate audio
└──────┬──────┘
       │ 2. Upload to S3
       ▼
┌─────────────┐
│AWS Transcribe│  Convert speech to text
└──────┬──────┘
       │ 3. Send via WebSocket
       ▼
┌─────────────────────────────────────────────────────────────┐
│              copilot_extension (VSCode)                      │
│                                                              │
│  WebSocket  ────▶  CopilotSession  ────▶  MessageProcessor │
│                          │                   (vv_context)    │
│                          │                        │          │
│                          ▼                        │          │
│                    VSCodeLanguageModel ◀──────────┘          │
│                    (GitHub Copilot)                          │
│                          │                                   │
│                          ▼                                   │
│                    AI generates code                         │
│                          │                                   │
│                          ▼                                   │
│                    VSCodeFileEditor                          │
│                    (writes to disk)                          │
└──────────────────────────┬───────────────────────────────────┘
                           │ 4. Return summary
                           ▼
                    ┌─────────────┐
                    │AWS Polly    │  Synthesize response
                    └──────┬──────┘
                           │ 5. Stream audio
                           ▼
                    ┌─────────────┐
                    │   iOS App   │  Play response
                    └─────────────┘
```

## Library Interface Contract

```typescript
// Define adapters for your environment
class YourLanguageModel implements ILanguageModel {
  async sendRequest(messages: IMessage[]): Promise<string> {
    // Call your AI provider (Copilot, Claude, OpenAI, etc.)
  }

  async isAvailable(): Promise<boolean> {
    // Check if AI is available
  }
}

class YourFileEditor implements IFileEditor {
  async writeFile(path: string, content: string): Promise<void> {
    // Write to filesystem
  }

  async readFile(path: string): Promise<string> {
    // Read from filesystem
  }

  async fileExists(path: string): Promise<boolean> {
    // Check file existence
  }

  async openInEditor(path: string): Promise<void> {
    // Open in editor (or log for CLI)
  }
}

class YourContextGatherer implements IContextGatherer {
  async getWorkspaceStructure(): Promise<string> {
    // Return file tree
  }

  async getRelevantFiles(keywords: string[]): Promise<Map<string, string>> {
    // Find and score relevant files
  }

  async getActiveFileContext(): Promise<string> {
    // Return active/current file info
  }
}

// Use the library
import { MessageProcessor } from '@vibevoice/context';

const processor = new MessageProcessor(
  new YourLanguageModel(),
  new YourFileEditor(),
  new YourContextGatherer()
);

const result = await processor.processMessage('Add error handling');
console.log(result.summary);       // "Added try-catch to getUserData"
console.log(result.editCount);     // 1
console.log(result.edits[0].filePath); // "src/api.ts"
```

## Context Gathering Flow

```
User Message: "Add error handling to getUserData"
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│            MessageProcessor.gatherContext()              │
└─────────────────────────────────────────────────────────┘
      │
      ├──▶ extractKeywords()
      │    ├─ "error"
      │    ├─ "handling"
      │    └─ "getUserData"
      │
      ├──▶ getWorkspaceStructure()
      │    └─ Returns file tree
      │
      ├──▶ getRelevantFiles([keywords])
      │    ├─ Scans all files
      │    ├─ Scores by keyword matches
      │    │   • Content match: +10 per occurrence
      │    │   • Path match:    +50 per occurrence
      │    ├─ Sorts by score
      │    └─ Returns top 15 files
      │
      └──▶ getActiveFileContext()
           └─ Returns current file preview
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│              Augmented Message to AI                     │
│                                                          │
│  [WORKSPACE STRUCTURE]                                   │
│  src/api.ts                                              │
│  src/utils.ts                                            │
│  ...                                                     │
│                                                          │
│  Relevant files in workspace:                            │
│  === src/api.ts ===                                      │
│  function getUserData() { ... }                          │
│                                                          │
│  Currently viewing: src/api.ts                           │
│                                                          │
│  User request: Add error handling to getUserData        │
│                                                          │
│  [SYSTEM INSTRUCTIONS]                                   │
│  To edit files, use: EDIT_FILE: ... NEW_CONTENT: ...   │
└─────────────────────────────────────────────────────────┘
```

## File Edit Format

The AI uses structured markers to edit files:

```
EDIT_FILE: src/api.ts
NEW_CONTENT:
async function getUserData() {
  try {
    const response = await fetch('/api/user');
    return await response.json();
  } catch (error) {
    console.error('Failed to fetch user data:', error);
    throw error;
  }
}
END_EDIT

SUMMARY_START
Added try-catch error handling to getUserData function
SUMMARY_END
```

## Test Mode Flow

```
process.env.VIBEVOICE_TEST_MODE = 'true'
      │
      ▼
MessageProcessor.processMessage("Add error handling")
      │
      ├─ Check testMode flag ✓
      │
      ├─ Skip language model call
      │
      ├─ Skip context gathering
      │
      ├─ Return mock response:
      │  {
      │    summary: "Test mode: Received command 'Add error handling'",
      │    editCount: 0,
      │    edits: []
      │  }
      │
      └─ Exit (fast, no AI calls)

Benefits:
✅ Test infrastructure without AI costs
✅ Fast test execution
✅ CI/CD without Copilot access
✅ Development iteration
```

## Package Dependencies

```
copilot_extension/
├── package.json
│   └── dependencies:
│       ├── "@vibevoice/context": "file:../vv_context"  ← Local library
│       ├── "@vscode/chat-extension-utils"
│       └── "ws"
└── node_modules/
    └── @vibevoice/
        └── context/          ← Symlinked from ../vv_context/dist
            ├── index.js
            ├── index.d.ts
            └── core/

vv_context/
├── package.json
│   └── No runtime dependencies! (Pure TypeScript)
└── dist/                     ← Compiled output
    ├── index.js
    ├── index.d.ts
    └── core/
```

## Summary

- **Library** (`vv_context`): Reusable, AI-agnostic, testable core logic
- **Extension** (`copilot_extension`): Copilot-specific adapters + VSCode UI
- **Future** (`claude_cli`, `cursor_extension`): Just implement 3 interfaces!

**Code Reuse:** ~95% of business logic
**Time to add new provider:** ~2 hours
**Lines saved per integration:** 500+
