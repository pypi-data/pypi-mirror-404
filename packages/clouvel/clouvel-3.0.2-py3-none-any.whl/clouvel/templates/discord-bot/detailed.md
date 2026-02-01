# {PROJECT_NAME} Discord Bot PRD

> This document is law. If it's not here, don't build it. If it's here, you MUST build it.
>
> Created: {DATE}
> Version: 1.0

---

## 1. One-line Summary

**[Server/Community Type]**'s **[Core Function]** Discord Bot

Example: "Match-making and stats tracking bot for gaming servers"

---

## 2. Core Principles

> 3 rules that never change. Everything follows these.

1. **[Principle 1]**: e.g., "Slash commands only, no prefix commands"
2. **[Principle 2]**: e.g., "Respond within 3 seconds or show 'thinking'"
3. **[Principle 3]**: e.g., "Never store message content"

---

## 3. Problem Definition

### 3.1 Current Problem

| Problem | Severity | Current Solution | Pain Point |
|---------|----------|------------------|------------|
| [Problem 1] | High/Medium/Low | [Existing method] | [Specific frustration] |
| [Problem 2] | | | |

### 3.2 This Bot's Solution

[How this bot solves the problem - be specific]

### 3.3 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Servers using bot | > X | Bot dashboard |
| Commands/day | > X | Logging |
| User satisfaction | > 4.5/5 | Feedback command |
| Uptime | > 99.9% | Monitoring |

---

## 4. Target Servers

### 4.1 Primary Server Profile

| Attribute | Value |
|-----------|-------|
| Server Type | [e.g., Gaming community, Study group] |
| Size | [e.g., 100-1000 members] |
| Activity Pattern | [e.g., Peak at evening hours] |
| Existing Bots | [e.g., MEE6, Dyno - no conflict expected] |

### 4.2 User Roles

| Role | Permissions | Primary Use Cases |
|------|-------------|-------------------|
| Server Owner | All commands | Setup, configuration |
| Admin | Management commands | Moderate, configure |
| Moderator | Moderation commands | Warn, mute, kick |
| Regular Member | Basic commands | Query, participate |
| New Member | Limited commands | View, basic interaction |

### 4.3 Aha Moment

> The moment server realizes value. Must happen within first hour of setup.

**Trigger**: [What action]
**Result**: [What they see]
**Time to Aha**: < X minutes after invite

Example: "Admin runs /setup → bot auto-detects server type → suggests optimal configuration → first match created in 5 minutes"

---

## 5. Command Specification

### P0 (Must Have) - No launch without these

#### Command: /[command-name]

**Purpose**: [Why this command exists]

**Syntax**:
```
/command-name <required_arg> [optional_arg]
```

**Input Specification**:
```typescript
interface CommandInput {
  name: 'command-name';
  options: {
    required_arg: {
      type: 'STRING' | 'INTEGER' | 'USER' | 'CHANNEL' | 'ROLE';
      required: true;
      description: string;
      choices?: Array<{ name: string; value: string }>;
      min_value?: number;
      max_value?: number;
    };
    optional_arg?: {
      type: 'STRING';
      required: false;
      description: string;
      default: string;
    };
  };
  context: {
    guild_id: string;
    channel_id: string;
    user_id: string;
    member_permissions: string[];
  };
}
```

**Output Specification**:
```typescript
interface CommandResponse {
  type: 'EMBED' | 'MESSAGE' | 'MODAL' | 'EPHEMERAL';
  content?: string;
  embed?: {
    title: string;
    description: string;
    color: number;  // 0x5865F2 = Discord Blurple
    fields?: Array<{
      name: string;
      value: string;
      inline?: boolean;
    }>;
    footer?: { text: string; icon_url?: string };
    timestamp?: string;
  };
  components?: Array<ActionRow>;
}
```

**Permission Required**: [e.g., MANAGE_MESSAGES, None]

**Rate Limit**: [e.g., 5 per minute per user]

**State Machine**:
```
[Received] --validate--> [Check Permissions] --pass--> [Execute]
                                            \--fail--> [Permission Error]
           \--invalid--> [Validation Error]

[Execute] --success--> [Send Response] --done--> [Log]
         \--error--> [Error Response] --done--> [Log]
```

**Error Cases**:

| Situation | Error Code | Response | Recovery |
|-----------|------------|----------|----------|
| Missing permission | E_PERM_001 | "You need [permission] to use this" | Show required permission |
| Invalid argument | E_ARG_001 | "Invalid value for [arg]" | Show valid options |
| Not in server | E_GUILD_001 | "This command only works in servers" | - |
| Rate limited | E_RATE_001 | "Slow down! Try again in X seconds" | Auto ephemeral |
| Bot lacks permission | E_BOT_001 | "I need [permission] to do this" | Show setup instructions |
| Target not found | E_404_001 | "[User/Channel/Role] not found" | - |
| Already exists | E_DUP_001 | "[Item] already exists" | Suggest edit command |
| Database error | E_DB_001 | "Something went wrong, try again" | Log full error internally |

**Test Scenarios**:
- [ ] Normal: Valid args, proper permissions → Success response
- [ ] Edge: Max length args → Handled correctly
- [ ] Error: Missing required arg → Clear error message
- [ ] Error: No permission → Ephemeral permission error
- [ ] Edge: Rapid fire (10 requests) → Rate limited properly
- [ ] Edge: Bot restarted mid-command → Graceful recovery

---

#### Command: /help

**Purpose**: Show available commands and usage

**Subcommands**:
- `/help` - Show command categories
- `/help [command]` - Show specific command details

**Response Format**:
```
📚 **{BOT_NAME} Help**

**Categories:**
• 🎮 `Games` - Match, stats, leaderboard
• ⚙️ `Config` - Server settings
• 🛡️ `Moderation` - Warn, mute, kick

Use `/help [category]` for details
```

---

#### Command: /[next command]

[Same structure as above]

---

### P1 (Should Have)

| Command | Description | Permission | Depends On |
|---------|-------------|------------|------------|
| /[command] | [Description] | [Permission] | P0 complete |

### P2 (Nice to Have)

| Command | Description | Notes |
|---------|-------------|-------|
| /[command] | [Description] | [For v2] |

---

## 6. Constraints (AI Boundaries)

### ALWAYS (Must Execute)
- [ ] Use Slash Commands (no prefix commands)
- [ ] Check permissions before execution
- [ ] Respect Discord rate limits
- [ ] Show "thinking" for operations > 3 seconds
- [ ] Log all command executions
- [ ] Defer response if processing > 2 seconds
- [ ] Use ephemeral messages for errors/sensitive info

### ASK FIRST (Confirm Before)
- [ ] Adding new Intents
- [ ] Adding DM functionality
- [ ] External API integration
- [ ] Storing user data beyond settings

### NEVER (Absolutely Forbidden)
- [ ] **Implement commands not in this spec**
- [ ] Hardcode tokens or secrets
- [ ] Make unlimited API calls
- [ ] Modify server settings without admin permission
- [ ] Send spam or unsolicited DMs
- [ ] Store message content
- [ ] Ignore rate limits (risk ban)

### Out of Scope
- Voice features - Reason: v2
- Multi-language - Reason: English first
- Web dashboard - Reason: Separate project

---

## 7. Bot Configuration

### 7.1 Required Intents

| Intent | Reason | Required |
|--------|--------|----------|
| GUILDS | Server information | Yes |
| GUILD_MEMBERS | Member info for commands | If needed |
| GUILD_MESSAGES | Message tracking | If needed |
| MESSAGE_CONTENT | Prefix commands | No (slash only) |

### 7.2 Required Permissions

| Permission | Reason | Numeric |
|------------|--------|---------|
| Send Messages | Respond to commands | 0x800 |
| Embed Links | Rich embeds | 0x4000 |
| Read Message History | Reference previous | 0x10000 |
| Use Slash Commands | Register commands | 0x80000000 |
| Add Reactions | Reaction-based UX | 0x40 |
| Manage Messages | Delete user commands | 0x2000 |

**Invite URL Permission Integer**: [Calculate from above]

### 7.3 Application Commands Scope

```
applications.commands - Required for slash commands
bot - Required for bot user
```

---

## 8. Response Formats

### 8.1 Embed Templates

**Success Embed**:
```javascript
{
  title: "✅ Success",
  description: "[What happened]",
  color: 0x57F287,  // Green
  footer: { text: "{BOT_NAME}" },
  timestamp: new Date().toISOString()
}
```

**Warning Embed**:
```javascript
{
  title: "⚠️ Warning",
  description: "[What to be aware of]",
  color: 0xFEE75C,  // Yellow
  footer: { text: "{BOT_NAME}" }
}
```

**Error Embed**:
```javascript
{
  title: "❌ Error",
  description: "[What went wrong]",
  color: 0xED4245,  // Red
  fields: [
    { name: "How to fix", value: "[Instructions]" }
  ],
  footer: { text: "Error Code: E_XXX_001" }
}
```

**Info Embed**:
```javascript
{
  title: "ℹ️ Information",
  description: "[Details]",
  color: 0x5865F2,  // Discord Blurple
  footer: { text: "{BOT_NAME}" }
}
```

### 8.2 Interactive Components

**Button Types**:
```typescript
type ButtonStyle =
  | 'PRIMARY'   // Blue, main action
  | 'SECONDARY' // Grey, alternative
  | 'SUCCESS'   // Green, confirm
  | 'DANGER'    // Red, destructive
  | 'LINK';     // URL redirect
```

**Select Menu**:
```typescript
interface SelectMenu {
  custom_id: string;
  placeholder: string;
  min_values: number;
  max_values: number;
  options: Array<{
    label: string;
    value: string;
    description?: string;
    emoji?: string;
  }>;
}
```

### 8.3 Response Timing

| Situation | Response Type | Timing |
|-----------|--------------|--------|
| Quick query | Immediate reply | < 1s |
| Database lookup | Deferred, then edit | 1-3s |
| External API | "Thinking..." indicator | > 3s |
| Long operation | Progress updates | > 10s |

---

## 9. Data Model

### 9.1 Database Schema

```sql
-- Guild settings (per-server configuration)
CREATE TABLE guild_settings (
  guild_id VARCHAR(20) PRIMARY KEY,
  prefix VARCHAR(10) DEFAULT '!',  -- Legacy, kept for migration
  language VARCHAR(5) DEFAULT 'en',
  timezone VARCHAR(50) DEFAULT 'UTC',
  features JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- User data (minimal, no message content)
CREATE TABLE users (
  user_id VARCHAR(20) PRIMARY KEY,
  guild_id VARCHAR(20),
  points INTEGER DEFAULT 0,
  level INTEGER DEFAULT 1,
  last_active TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (guild_id) REFERENCES guild_settings(guild_id)
);

-- Command logs (for analytics, no sensitive data)
CREATE TABLE command_logs (
  id SERIAL PRIMARY KEY,
  guild_id VARCHAR(20),
  user_id VARCHAR(20),
  command VARCHAR(50),
  success BOOLEAN,
  execution_time_ms INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 9.2 Cache Strategy

| Data Type | Cache Location | TTL | Invalidation |
|-----------|----------------|-----|--------------|
| Guild settings | Memory (Map) | 5 min | On update |
| User data | Redis | 10 min | On level up |
| Rate limits | Memory | 60s | Auto expire |
| Command registry | Memory | - | On restart |

### 9.3 Data Retention

| Data Type | Retention | Reason |
|-----------|-----------|--------|
| Guild settings | Until bot removed | Configuration |
| User stats | Until user requests deletion | Features |
| Command logs | 30 days | Analytics |
| Error logs | 7 days | Debugging |

---

## 10. Tech Stack

| Category | Choice | Reason |
|----------|--------|--------|
| Language | Node.js / Python | [Reason] |
| Library | discord.js / discord.py | [Reason] |
| Database | PostgreSQL / SQLite | [Reason] |
| Cache | Redis / Memory | [Reason] |
| Hosting | Railway / Heroku / VPS | [Reason] |
| Monitoring | UptimeRobot / Better Stack | [Reason] |

---

## 11. Error Handling

### 11.1 Error Hierarchy

```
BotError (base)
├── CommandError
│   ├── ValidationError (invalid input)
│   ├── PermissionError (user lacks permission)
│   └── ExecutionError (command failed)
├── ApiError
│   ├── RateLimitError (Discord rate limit)
│   ├── NetworkError (connection failed)
│   └── ServiceError (external API failed)
└── DatabaseError
    ├── ConnectionError
    └── QueryError
```

### 11.2 Error Responses by Type

| Error Type | User Sees | Logged | Alert |
|------------|-----------|--------|-------|
| Validation | Ephemeral message | No | No |
| Permission | Ephemeral message | Yes | No |
| Rate limit | Ephemeral + wait time | Yes | If frequent |
| Database | Generic error | Full stack | Yes |
| Unhandled | "Something went wrong" | Full stack | Yes |

### 11.3 Graceful Degradation

| Failure | Fallback Behavior |
|---------|-------------------|
| Database down | Read from cache, queue writes |
| Redis down | Use memory cache |
| External API down | Show cached data or skip feature |
| Rate limited | Queue and retry |

---

## 12. Event Handlers

### 12.1 Core Events

| Event | Handler | Action |
|-------|---------|--------|
| ready | onReady | Log startup, set status |
| interactionCreate | onInteraction | Route to command handler |
| guildCreate | onGuildJoin | Log, send welcome, register commands |
| guildDelete | onGuildLeave | Clean up data (optional) |
| error | onError | Log, alert if critical |

### 12.2 Interaction Flow

```
interactionCreate
    │
    ├── isCommand? → CommandHandler
    │                    ├── validateInput()
    │                    ├── checkPermissions()
    │                    ├── execute()
    │                    └── logCommand()
    │
    ├── isButton? → ButtonHandler
    │                    └── handleClick()
    │
    ├── isSelectMenu? → SelectHandler
    │                    └── handleSelection()
    │
    └── isModal? → ModalHandler
                     └── handleSubmit()
```

---

## 13. Security Considerations

### 13.1 Token Security

- [ ] Token in environment variable, never in code
- [ ] .env in .gitignore
- [ ] Rotate token if exposed
- [ ] Use secrets manager in production

### 13.2 Permission Checks

```typescript
// Every command must check:
function checkPermissions(interaction: CommandInteraction): boolean {
  // 1. Bot has required permissions
  // 2. User has required permissions
  // 3. Command is allowed in this channel type
  // 4. Rate limit not exceeded
}
```

### 13.3 Input Validation

- [ ] Sanitize all user inputs
- [ ] Validate snowflake IDs (user, channel, role)
- [ ] Limit string lengths
- [ ] Escape special characters in output
- [ ] Never eval() user input

---

## 14. Edge Cases

| Situation | Expected Behavior | Test Case |
|-----------|-------------------|-----------|
| Bot added with no permissions | Send DM to admin with setup | Invite with 0 permissions |
| Command in DM | "This command only works in servers" | DM the bot |
| User spam commands | Rate limit, ephemeral warning | 20 commands in 10s |
| Bot restarted mid-interaction | Expire gracefully | Kill process during command |
| Guild deleted bot data | Keep or delete based on setting | Remove bot from server |
| Concurrent same command | Handle properly, no race conditions | Parallel /stats calls |
| Very large server (10k+) | Pagination, async operations | Mock large member count |
| Invalid snowflake input | "Invalid ID format" | Random string as user ID |

---

## 15. Performance Requirements

| Metric | Target | Measurement |
|--------|--------|-------------|
| Command response time | < 500ms (p95) | Logging |
| Startup time | < 10s | Process timing |
| Memory usage | < 512MB | Process metrics |
| Database queries/command | < 3 | Query logging |
| Concurrent guilds | > 1000 | Load testing |

---

## 16. Definition of Done (DoD)

### Feature DoD
- [ ] All test scenarios pass
- [ ] Error cases return user-friendly messages
- [ ] Permissions checked before execution
- [ ] Rate limits implemented
- [ ] Command logged for analytics

### Quality DoD
- [ ] Discord ToS compliant
- [ ] Rate limit handling (no 429 spam)
- [ ] Memory stable over 24 hours
- [ ] Graceful restart/shutdown

### Release DoD
- [ ] Bot invite link tested
- [ ] /help command complete
- [ ] Setup documentation written
- [ ] Monitoring configured
- [ ] Backup/restore tested

---

## 17. Deployment

### 17.1 Environment Variables

```bash
# Required
DISCORD_TOKEN=your_bot_token
DISCORD_CLIENT_ID=your_client_id

# Optional
DATABASE_URL=postgres://...
REDIS_URL=redis://...
LOG_LEVEL=info
NODE_ENV=production
```

### 17.2 Startup Checklist

```typescript
// On startup, verify:
1. [ ] Token valid (test API call)
2. [ ] Database connected
3. [ ] Cache initialized
4. [ ] Commands registered
5. [ ] Event handlers attached
6. [ ] Health endpoint responding
```

### 17.3 Health Check

```typescript
// GET /health
{
  status: 'ok' | 'degraded' | 'down',
  uptime: number,
  guilds: number,
  ping: number,  // Discord Gateway latency
  database: 'connected' | 'error',
  cache: 'connected' | 'error'
}
```

---

## 18. Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| {DATE} | 1.0 | Initial draft | |
