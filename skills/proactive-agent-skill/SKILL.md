---
name: proactive-agent-skill
description: Transform AI agents from task-followers into proactive partners that anticipate needs and continuously improve. Includes WAL Protocol, Working Buffer, Autonomous Crons, and Heartbeat checks.
---

# Proactive Agent Skill

Transform AI agents from task-followers into proactive partners that anticipate needs and continuously improve.

## When to Use

✅ **USE this skill when:**
- "Make the agent more proactive"
- "Automate routine checks"
- "Implement memory persistence"
- "Schedule automated tasks"
- "Build self-improving agents"

## Core Architecture

### 1. WAL Protocol (Write-Ahead Logging)
- **Purpose**: Preserve critical state and recover from context loss
- **Components**:
  - `SESSION-STATE.md` - Active working memory (current task)
  - `working-buffer.md` - Danger zone log
  - `MEMORY.md` - Long-term curated memory

### 2. Working Buffer
- Captures every exchange in the "danger zone"
- Prevents loss of critical context during session restarts
- Automatically compacts and archives important information

### 3. Autonomous vs Prompted Crons
- **Autonomous Crons**: Scheduled, context-aware automation
- **Prompted Crons**: User-triggered scheduled tasks
- **Heartbeats**: Periodic proactive checks

## Implementation Patterns

### Memory Architecture
```
workspace/
├── MEMORY.md            # Long-term curated memory
├── memory/
│   └── YYYY-MM-DD.md    # Daily raw logs
├── SESSION-STATE.md     # Active working memory
└── working-buffer.md    # Danger zone log
```

### WAL Protocol Workflow
- **Capture**: Log all critical exchanges to working buffer
- **Compact**: Periodically review and extract key insights
- **Curate**: Move important information to MEMORY.md
- **Recover**: Restore state from logs after restart

### Proactive Behaviors

#### 1. Heartbeat Checks
```
# Check every 30 minutes
- Email inbox for urgent messages
- Calendar for upcoming events
- Weather for relevant conditions
- System status and health
```

#### 2. Autonomous Crons
```
# Daily maintenance
- Memory compaction and cleanup
- File organization
- Backup verification
# Weekly tasks
- Skill updates check
- Documentation review
- Performance optimization
```

#### 3. Context-Aware Automation
- Detect patterns in user requests
- Anticipate follow-up needs
- Suggest relevant actions

## Configuration

### Basic Setup
- Create memory directory structure
- Set up SESSION-STATE.md template
- Configure heartbeat intervals
- Define autonomous cron schedules

### Advanced Configuration
```json
{
  "proactive": {
    "heartbeatInterval": 1800,
    "autonomousCrons": {
      "daily": ["08:00", "20:00"],
      "weekly": ["Monday 09:00"]
    },
    "memory": {
      "compactionThreshold": 1000,
      "retentionDays": 30
    }
  }
}
```

## Best Practices

### 1. Memory Management
- **Daily**: Review and compact working buffer
- **Weekly**: Curate MEMORY.md from daily logs
- **Monthly**: Archive and cleanup old files

### 2. Proactive Behavior
- **Anticipate**: Look for patterns in requests
- **Suggest**: Offer relevant next steps
- **Automate**: Create crons for repetitive tasks

### 3. Error Recovery
- **Log everything**: Critical details to working buffer
- **Graceful degradation**: Fallback when components fail
- **Self-healing**: Automatic recovery from errors

## Credits
Created by Hal 9001 (@halthelobster).
Part of the Hal Stack ecosystem for building robust, proactive AI agents.
