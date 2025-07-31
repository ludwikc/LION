# LION Discord Bot - Commands Manual

LION is a Discord bot that tracks activities while offering productivity tools like to-do lists, pomodoro timers, reminders, and statistics. This manual lists all available commands organized by permission level.

## 📋 Table of Contents

- [User Commands](#-user-commands-no-special-permissions)
- [Low Management Commands](#-low-management-commands)
- [High Management Commands](#-high-management-commands)  
- [System Admin Commands](#-system-admin-commands)

---

## 👤 User Commands (No Special Permissions)

These commands are available to all server members.

### Personal Profile & Statistics

- **`/me`** - Edit your personal profile and see your statistics
- **`/profile [member]`** - Display a member's profile and statistics summary
- **`/stats`** - View your weekly and monthly activity statistics
- **`/achievements`** - View your progress towards activity achievement awards

### Server Information

- **`/leaderboard`** - View the server activity leaderboard
- **`/ranks`** - View the server rank system overview

### Customization

- **`/my skin`** - Change the colors and appearance of your interface

### Productivity Tools

#### Pomodoro Timers
- **`/pomodoro create <focus_length> <break_length> [channel]`** - Create a new Pomodoro timer
  - `focus_length`: Work session length in minutes (1-1440)
  - `break_length`: Break length in minutes (1-1440)  
  - `channel`: Voice channel for the timer (optional)
- **`/pomodoro join [timer]`** - Join an existing Pomodoro timer
- **`/pomodoro leave`** - Leave your current Pomodoro timer

#### Task Lists
- **`/tasklist add <task> [category]`** - Add a new task to your list
- **`/tasklist remove <task_id>`** - Remove a task from your list
- **`/tasklist list [category]`** - View your task list
- **`/tasklist done <task_id>`** - Mark a task as completed
- **`/tasklist edit <task_id> <new_description>`** - Edit an existing task
- **`/tasklist clear [category]`** - Clear completed tasks
- **`/tasklist categories`** - View your task categories

#### Reminders
- **`/remind <time> <message>`** - Set a personal reminder
- **`/remindme list`** - View your active reminders
- **`/remindme cancel <reminder_id>`** - Cancel a reminder

### Economy System

- **`/economy balance [target]`** - View LionCoin balance for yourself or others
- **`/shop`** - Browse and purchase items with LionCoins

### Voice Features

- **`/queue`** - Join the voice channel queue system

### Other Tools

- **`/secret <message>`** - Send an anonymous message (Polish language support)
- **`/vent <message>`** - Send to the venting channel (Polish language support)

---

## 🛡️ Low Management Commands

These commands require low-level management permissions in the server.

### Room Management

- **`/room create <name> [capacity] [category]`** - Create a temporary room
- **`/room delete <room>`** - Delete a temporary room  
- **`/room edit <room>`** - Edit room settings
- **`/room transfer <room> <new_owner>`** - Transfer room ownership
- **`/room ban <room> <member>`** - Ban a member from a room
- **`/room unban <room> <member>`** - Unban a member from a room

### User Configuration

- **`/my timezone <timezone>`** - Set your timezone
- **`/my config`** - Access your personal configuration settings

---

## ⚔️ High Management Commands

These commands require high-level management permissions in the server.

### Server Configuration

- **`/configure statistics`** - Configure server statistics settings
- **`/configure economy`** - Configure server economy settings
- **`/configure pomodoro`** - Configure Pomodoro timer settings
- **`/configure tasklist`** - Configure task list settings
- **`/configure schedule`** - Configure session scheduling
- **`/configure moderation`** - Configure moderation settings
- **`/configure video_channels`** - Configure video channel settings
- **`/configure ranks`** - Configure the rank system
- **`/configure rooms`** - Configure room system settings

### Advanced Moderation

- **`/admin note <member> <note>`** - Add a note to a member's record
- **`/admin warn <member> <reason>`** - Issue a warning to a member

### Role Management

- **`/rolemenu create <name>`** - Create a new role menu
- **`/rolemenu delete <menu>`** - Delete a role menu
- **`/rolemenu edit <menu>`** - Edit role menu settings
- **`/rolemenu roles <menu>`** - Manage roles in a menu
- **`/rolemenu preview <menu>`** - Preview how a role menu will look
- **`/rolemenu post <menu> [channel]`** - Post a role menu to a channel

### Brand Customization

- **`/admin brand`** - Customize server interface branding (Premium feature - currently disabled)

---

## 🔧 System Admin Commands

These commands are restricted to bot system administrators only.

### Bot Management

- **`/leo skin [default_skin]`** - View and update global skin settings
- **`/leo dash`** - Access the system administration dashboard
- **`/leo blacklist <action>`** - Manage bot blacklists

### Development Tools

- **`/async <code> [target]`** - Execute arbitrary code across shards
- **`/shell <command>`** - Execute shell commands on the bot server
- **`/reload <module>`** - Reload bot modules
- **`/shutdown`** - Safely shutdown the bot
- **`/restart`** - Restart the bot

### System Configuration

- **`/configure presence`** - Configure bot presence and status
- **`/configure general`** - Configure general bot settings

---

## 📖 Usage Notes

### Command Syntax
- `<required>` - Required parameters
- `[optional]` - Optional parameters  
- `<choice1|choice2>` - Choose one of the provided options

### Permissions
- **User Commands**: Available to all server members
- **Low Management**: Requires basic moderation permissions
- **High Management**: Requires administrator or high-level management permissions
- **System Admin**: Bot owner/developer access only

### Special Features

#### Activity Tracking
LION automatically tracks your study time, message activity, and voice channel participation. Use `/me`, `/stats`, and `/profile` to view your progress.

#### Economy System
Earn LionCoins through activity and spend them in the `/shop` on ranks, roles, and other rewards.

#### Pomodoro Timers
Create focused work sessions with built-in break timers. Perfect for study groups and productivity sessions.

#### Task Management
Keep track of your goals and tasks with categories and progress tracking.

### Getting Help

For additional help with any command, you can:
1. Use Discord's built-in slash command help (start typing `/` and browse)
2. Contact server administrators for permission-related questions
3. Report issues to the bot development team

---

*Last updated: July 2025*
*LION Bot - Productivity and Activity Tracking for Discord*