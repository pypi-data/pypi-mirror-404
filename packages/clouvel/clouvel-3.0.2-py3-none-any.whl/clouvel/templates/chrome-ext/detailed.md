# {PROJECT_NAME} Chrome Extension PRD

> This document is law. If it's not here, don't build it. If it's here, you MUST build it.
>
> Created: {DATE}
> Version: 1.0

---

## 1. One-line Summary

**[Target User]**'s **[Core Function]** Chrome Extension

Example: "Price comparison automation extension for online shoppers"

---

## 2. Core Principles

> 3 rules that never change. Everything follows these.

1. **[Principle 1]**: e.g., "Minimum permissions only"
2. **[Principle 2]**: e.g., "Zero data collection without consent"
3. **[Principle 3]**: e.g., "Works offline first"

---

## 3. Problem Definition

### 3.1 Current Problem

| Problem | Severity | Current Solution | Pain Point |
|---------|----------|------------------|------------|
| [Problem 1] | High/Medium/Low | [Existing method] | [Specific frustration] |
| [Problem 2] | | | |

### 3.2 This Extension's Solution

[How this extension solves the problem - be specific]

### 3.3 Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Daily Active Users | > X | Chrome Analytics |
| User Rating | > 4.5 | Web Store |
| Retention D7 | > 40% | Analytics |
| Feature Usage | > 60% | Event tracking |

---

## 4. Target Users

### 4.1 Primary User Persona

| Attribute | Value |
|-----------|-------|
| Who | [e.g., Office workers] |
| Browser Usage | [e.g., 8+ hours daily] |
| Tech Level | [e.g., Intermediate] |
| Pain Frequency | [e.g., 10+ times per day] |

### 4.2 Aha Moment

> The moment user realizes value. Must happen within first session.

**Trigger**: [What action]
**Result**: [What they see]
**Time to Aha**: < X seconds

Example: "User clicks extension icon → sees price comparison across 5 stores → realizes saved $20 in 3 seconds"

---

## 5. Core Features

### P0 (Must Have) - No launch without these

#### Feature 1: [Feature Name]

**Purpose**: [Why this feature exists]

**Input Specification**:
```typescript
interface FeatureInput {
  trigger: 'click' | 'auto' | 'keyboard';
  context: {
    url: string;
    selectedText?: string;
    pageContent?: string;
  };
}
```

**Output Specification**:
```typescript
interface FeatureOutput {
  success: boolean;
  data?: {
    result: string;
    metadata: Record<string, any>;
  };
  error?: {
    code: string;
    message: string;
  };
}
```

**State Machine**:
```
[Idle] --trigger--> [Processing] --success--> [Display Result]
                               \--error--> [Show Error] --> [Idle]
```

**Error Cases**:

| Situation | Error Code | User Message | Recovery |
|-----------|------------|--------------|----------|
| No permission | E_PERM_001 | "Permission required for this site" | Show permission request |
| Network failed | E_NET_001 | "Check your connection" | Retry button |
| Page not supported | E_PAGE_001 | "Not available on this site" | Show supported sites |
| Rate limited | E_RATE_001 | "Too many requests, wait X seconds" | Auto-retry after delay |
| Parse failed | E_PARSE_001 | "Couldn't read page content" | Manual input option |

**Test Scenarios**:
- [ ] Normal: Trigger on supported page → Result displays correctly
- [ ] Edge: Very long content → Truncated with "show more"
- [ ] Error: Unsupported page → Graceful error message
- [ ] Edge: User rapidly clicks → Debounced, no duplicate requests

---

#### Feature 2: [Feature Name]

[Same structure as Feature 1]

---

### P1 (Should Have)

| Feature | Description | Depends On | DoD |
|---------|-------------|------------|-----|
| [Feature 1] | [Description] | P0 complete | [Criteria] |

### P2 (Nice to Have)

| Feature | Description | Notes |
|---------|-------------|-------|
| [Feature 1] | [Description] | [For v2] |

---

## 6. Constraints (AI Boundaries)

### ALWAYS (Must Execute)
- [ ] Request minimum permissions only
- [ ] Store user data locally first (chrome.storage)
- [ ] Handle errors gracefully with user-friendly messages
- [ ] Minimize content script injection
- [ ] Show loading states for operations > 500ms
- [ ] Log actions for debugging (remove in production)

### ASK FIRST (Confirm Before)
- [ ] Adding new permissions
- [ ] External API integration
- [ ] Adding background processes
- [ ] Modifying existing functionality

### NEVER (Absolutely Forbidden)
- [ ] **Implement features not in this spec**
- [ ] Request unnecessary permissions
- [ ] Collect data without explicit consent
- [ ] Leave console.log in production
- [ ] Create infinite loops or memory leaks
- [ ] Make synchronous blocking calls
- [ ] Store sensitive data (passwords, tokens) unencrypted

### Out of Scope
- Firefox/Safari support - Reason: v2
- Dark mode - Reason: Follow system theme
- [Feature] - Reason: [Why excluded]

---

## 7. Extension Architecture

### 7.1 Manifest (MV3)

```json
{
  "manifest_version": 3,
  "name": "{PROJECT_NAME}",
  "version": "1.0.0",
  "description": "[150 char description]",
  "permissions": [
    "storage",
    "activeTab"
  ],
  "optional_permissions": [
    "[permission that can be requested later]"
  ],
  "host_permissions": [
    "*://*.example.com/*"
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "background": {
    "service_worker": "background/service-worker.js",
    "type": "module"
  },
  "content_scripts": [
    {
      "matches": ["*://*.example.com/*"],
      "js": ["content/content.js"],
      "run_at": "document_idle"
    }
  ]
}
```

### 7.2 Permission Matrix

| Permission | Reason | Required | When Requested |
|------------|--------|----------|----------------|
| storage | Save settings | Required | Install |
| activeTab | Access current tab | Required | Install |
| tabs | List all tabs | Optional | First use |
| [permission] | [reason] | [Required/Optional] | [timing] |

### 7.3 File Structure

```
/
├── manifest.json
├── popup/
│   ├── popup.html          # Popup UI
│   ├── popup.css           # Popup styles
│   └── popup.js            # Popup logic
├── content/
│   ├── content.js          # Content script (injected)
│   └── content.css         # Content styles
├── background/
│   └── service-worker.js   # Background worker (MV3)
├── options/
│   ├── options.html        # Settings page
│   └── options.js
├── lib/
│   └── utils.js            # Shared utilities
├── assets/
│   └── icons/
│       ├── icon16.png
│       ├── icon48.png
│       └── icon128.png
└── _locales/               # i18n (if needed)
    └── en/
        └── messages.json
```

---

## 8. Communication Flow

### 8.1 Message Passing

```
[Popup] <--chrome.runtime.sendMessage--> [Service Worker]
                                              |
                                    chrome.tabs.sendMessage
                                              |
                                              v
                                      [Content Script]
```

### 8.2 Message Types

```typescript
// Message from Popup to Background
interface PopupMessage {
  type: 'FETCH_DATA' | 'SAVE_SETTING' | 'GET_STATUS';
  payload: Record<string, any>;
}

// Message from Background to Content
interface ContentMessage {
  type: 'EXTRACT_DATA' | 'INJECT_UI' | 'CLEANUP';
  payload: Record<string, any>;
}

// Response format
interface MessageResponse {
  success: boolean;
  data?: any;
  error?: string;
}
```

### 8.3 Event Handling

| Event | Source | Handler | Action |
|-------|--------|---------|--------|
| Extension installed | chrome.runtime | service-worker | Show onboarding |
| Tab updated | chrome.tabs | service-worker | Check if supported |
| Icon clicked | chrome.action | popup.js | Open popup |
| [Event] | [Source] | [Handler] | [Action] |

---

## 9. UI Specification

### 9.1 Popup Layout

```
+---------------------------+
|  Logo    [Settings Icon]  |  <- Header (40px)
+---------------------------+
|                           |
|     [Main Content]        |  <- Main (variable)
|                           |
+---------------------------+
|  Status: Ready            |  <- Footer (24px)
+---------------------------+

Width: 320px (min) - 400px (max)
Height: 200px (min) - 600px (max)
```

### 9.2 State-based UI

| State | UI | Actions Available |
|-------|-----|-------------------|
| Inactive | "Not available on this site" | Link to supported sites |
| Loading | Spinner + "Processing..." | Cancel button |
| Success | Result display | Copy, Share, Refresh |
| Error | Error message (red) | Retry button |
| Offline | "You're offline" | Retry when online |

### 9.3 Component Specs

**Button Primary**:
- Background: #4285F4
- Text: White, 14px, Bold
- Padding: 12px 24px
- Border-radius: 8px
- Hover: darken 10%

**Button Secondary**:
- Background: transparent
- Border: 1px solid #DADCE0
- Text: #1A73E8, 14px
- Hover: background #F8F9FA

---

## 10. Data Storage

### 10.1 Storage Schema

```typescript
// chrome.storage.sync (synced across devices, 100KB limit)
interface SyncStorage {
  settings: {
    enabled: boolean;
    theme: 'light' | 'dark' | 'system';
    notifications: boolean;
    language: string;
  };
  preferences: {
    [key: string]: any;
  };
}

// chrome.storage.local (local only, 10MB limit)
interface LocalStorage {
  cache: {
    [key: string]: {
      data: any;
      timestamp: number;
      ttl: number;  // seconds
    };
  };
  history: Array<{
    action: string;
    timestamp: number;
    data: any;
  }>;
}
```

### 10.2 Storage Limits

| Storage Type | Limit | Use Case |
|--------------|-------|----------|
| sync | 100KB total, 8KB per item | Settings, preferences |
| local | 10MB | Cache, history |
| session | 10MB | Temporary state |

### 10.3 Data Migration

```typescript
// Version-based migration
const CURRENT_VERSION = 2;

async function migrateData() {
  const { version = 1 } = await chrome.storage.local.get('version');

  if (version < 2) {
    // Migration v1 -> v2
    const oldData = await chrome.storage.sync.get('oldKey');
    await chrome.storage.sync.set({ newKey: transform(oldData) });
    await chrome.storage.sync.remove('oldKey');
  }

  await chrome.storage.local.set({ version: CURRENT_VERSION });
}
```

---

## 11. Tech Stack

| Category | Choice | Reason |
|----------|--------|--------|
| Manifest | V3 | Chrome policy (required from 2024) |
| Framework | Vanilla / React / Vue | [Reason] |
| Bundler | Vite / Webpack | [Reason] |
| Styling | CSS / Tailwind | [Reason] |
| Testing | Jest / Vitest | [Reason] |
| TypeScript | Yes / No | [Reason] |

---

## 12. Security Considerations

### 12.1 Content Security Policy

```json
{
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  }
}
```

### 12.2 Security Checklist

- [ ] No inline scripts (CSP violation)
- [ ] No eval() or new Function()
- [ ] Sanitize all user inputs
- [ ] Validate all external data
- [ ] Use HTTPS for all requests
- [ ] No sensitive data in console.log
- [ ] Content scripts isolated properly

### 12.3 Privacy

| Data Type | Collected | Purpose | Retention |
|-----------|-----------|---------|-----------|
| Usage stats | Yes/No | [Purpose] | [Days] |
| User settings | Local only | Personalization | Until uninstall |
| [Data] | [Yes/No] | [Purpose] | [Retention] |

---

## 13. Edge Cases

| Situation | Expected Behavior | Test Case |
|-----------|-------------------|-----------|
| Unsupported site | Show message, no errors | Visit non-matching URL |
| Permission denied | Show permission request | Reject permission prompt |
| Network offline | Use cache or show offline UI | Disconnect network |
| Page loading | Wait for document_idle | Slow loading page |
| Extension updated | Migrate data, notify user | Simulate update |
| Multiple tabs | Handle concurrent requests | Open same site in 5 tabs |
| Very slow page | Timeout after Xs, show error | Throttle network |
| User spam clicks | Debounce, single request | Rapid clicking |

---

## 14. Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Popup open time | < 100ms | Performance API |
| Content script injection | < 50ms | Performance API |
| Memory usage | < 50MB | Chrome Task Manager |
| CPU idle | < 1% | Chrome Task Manager |
| Storage usage | < 5MB | chrome.storage.getBytesInUse |

---

## 15. Definition of Done (DoD)

### Feature DoD
- [ ] All test scenarios pass
- [ ] Error cases handled with user-friendly messages
- [ ] Loading states for operations > 500ms
- [ ] Works on all P0 supported sites
- [ ] No console errors
- [ ] Memory stable after 1 hour use

### Quality DoD
- [ ] Chrome Web Store policy compliance
- [ ] No memory leaks (verified with DevTools)
- [ ] Lighthouse score > 90
- [ ] Tested on Chrome Stable + Beta

### Release DoD
- [ ] Store listing complete (description, screenshots)
- [ ] Privacy policy published
- [ ] Icons all sizes ready (16, 48, 128, 256)
- [ ] Version number incremented

---

## 16. Web Store Listing

### 16.1 Required Assets

| Asset | Size | Notes |
|-------|------|-------|
| Icon | 128x128 | PNG, no alpha outside circle |
| Promo Small | 440x280 | Optional but recommended |
| Screenshot | 1280x800 or 640x400 | Min 1, max 5 |
| Promo Video | YouTube URL | Optional |

### 16.2 Description Template

```
Short Description (132 chars max):
[Core value proposition in one line]

Detailed Description:
[Problem]
[Solution - what your extension does]
[Key features - bullet points]
[Privacy statement]
```

---

## 17. Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| {DATE} | 1.0 | Initial draft | |
