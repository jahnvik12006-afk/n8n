Product Requirements Document (PRD)

Project Name

HisuClaw

Version: 2.0

Status: Planning

Language: Python 3.12+

Architecture:

- FastAPI
- AI Agent
- MCP-style Tool System
- Telegram Bot
- YouTube Data API
- YouTube Analytics API
- Groq LLM
- SQLite
- Render Deployment

---

Purpose

HisuClaw is an AI-powered YouTube Channel Management Agent designed specifically for Hindi:

- Manhwa Recaps
- Manhua Recaps
- Manga Recaps

channels.

The system helps channel owners:

- Analyze performance
- Analyze growth
- Analyze CTR
- Analyze retention
- Analyze competitors
- Generate SEO improvements
- Generate content strategies
- Generate title suggestions
- Generate description suggestions
- Generate tag suggestions

while preventing unauthorized modifications.

---

Core Principles

Principle 1

AI may read channel data at any time.

Principle 2

AI may never modify channel data without explicit user approval.

Principle 3

Every modification requires confirmation.

Principle 4

Every modification generates execution logs.

Principle 5

Only Telegram Admin may access the system.

Principle 6

All secrets must be stored inside .env.

Principle 7

AI memory retention limited to previous 24 hours only.

---

Target User

Single Owner

Single YouTube Channel

Single Telegram Admin

---

AI Provider

Primary:

Groq

Supported Models:

Provider Router automatically selects best available model.

Priority:

1. Latest DeepSeek Reasoning Model
2. Latest Qwen Reasoning Model
3. Latest Llama Reasoning Model

Fallback Routing:

If primary model fails:

Automatically switch provider.

---

AI Responsibilities

Allowed:

- Analyze channel
- Analyze videos
- Analyze audience
- Analyze retention
- Analyze CTR
- Analyze tags
- Analyze descriptions
- Analyze competitors
- Generate strategies
- Generate reports
- Recommend improvements

Forbidden:

- Update titles
- Update descriptions
- Update tags

unless admin explicitly confirms.

---

Environment Variables

.env

YOUTUBE_CLIENT_ID=

YOUTUBE_CLIENT_SECRET=

YOUTUBE_REFRESH_TOKEN=

TELEGRAM_BOT_TOKEN=

TELEGRAM_ADMIN_ID=

GROQ_API_KEY=

GROQ_BASE_URL=

AUTHORIZATION_TOKEN=

PORT=8000

MEMORY_RETENTION_HOURS=24

---

Authentication

All API endpoints require:

Authorization Header

Example:

Authorization: Bearer TOKEN

Invalid:

HTTP 401

---

Telegram Security

Only one Telegram User ID allowed.

Validation:

incoming_user_id == TELEGRAM_ADMIN_ID

If false:

Access Denied

No AI Execution

No Tool Execution

No Analytics Access

---

Memory System

Retention:

24 Hours

Storage:

SQLite

Stored:

- Reports
- Analysis Results
- Recommendations
- Executed Changes

Auto Cleanup:

Every 1 Hour

Delete Records Older Than:

24 Hours

---

MCP Tool System

Every Tool Contains:

- name
- description
- permissions
- input_schema
- output_schema
- execution_log

---

READ TOOLS

AnalyzeChannel

Permission:

READ

Capabilities:

- Channel Overview
- Views
- Subscribers
- Watch Time
- Revenue Eligibility
- Upload Frequency

Endpoint:

/api/analyze/channel

---

AnalyzeVideos

Permission:

READ

Capabilities:

- List Videos
- Performance Ranking

Endpoint:

/api/analyze/videos

---

AnalyzeVideo

Permission:

READ

Capabilities:

- Single Video Audit
- SEO Audit
- CTR Audit

Endpoint:

/api/analyze/video/{id}

---

AnalyzeRetention

Permission:

READ

Capabilities:

- Retention Graph
- Drop Detection
- Hook Analysis

Endpoint:

/api/analyze/retention

---

AnalyzeCTR

Permission:

READ

Capabilities:

- CTR
- CTR Trend
- CTR Suggestions

Endpoint:

/api/analyze/ctr

---

AnalyzeAudience

Permission:

READ

Capabilities:

- Geography
- Devices
- Returning Viewers
- New Viewers

Endpoint:

/api/analyze/audience

---

AnalyzeGrowth

Permission:

READ

Capabilities:

- Growth Trend
- Subscriber Growth
- View Growth

Endpoint:

/api/analyze/growth

---

AnalyzeSEO

Permission:

READ

Capabilities:

- Title Quality
- Description Quality
- Tags Quality
- Keyword Opportunity

Endpoint:

/api/analyze/seo

---

AnalyzeCompetitors

Permission:

READ

Capabilities:

- Competitor Titles
- Competitor Descriptions
- Competitor Tags
- Competitor Upload Frequency
- Competitor Topics
- Competitor Views

AI will NOT analyze actual video content.

AI will analyze:

- Metadata
- Views
- Publishing Patterns

Endpoint:

/api/analyze/competitors

---

GENERATION TOOLS

GenerateTitles

Creates:

- CTR Optimized Titles
- Hindi Audience Titles

---

GenerateDescriptions

Creates:

- SEO Descriptions

---

GenerateTags

Creates:

- SEO Tags

---

GenerateSeriesIdeas

Creates:

- New Series Ideas
- Trending Recap Topics

---

GenerateContentStrategy

Creates:

- Weekly Plan
- Monthly Plan

---

WRITE TOOLS

UpdateTitle

Permission:

WRITE

Endpoint:

/api/update-title

Flow:

1. Generate Suggestion
2. Send Telegram Confirmation
3. Wait Confirmation
4. Execute

---

UpdateDescription

Permission:

WRITE

Endpoint:

/api/update-description

Flow:

1. Generate Suggestion
2. Send Telegram Confirmation
3. Wait Confirmation
4. Execute

---

UpdateTags

Permission:

WRITE

Endpoint:

/api/update-tags

Flow:

1. Generate Suggestion
2. Send Telegram Confirmation
3. Wait Confirmation
4. Execute

---

Confirmation Workflow

Telegram Message:

Title Update Request

Current:

XYZ

Suggested:

ABC

Buttons:

[CONFIRM]

[DECLINE]

Only after CONFIRM:

Tool executes.

DECLINE:

Request cancelled.

---

Competitor Intelligence

AI must:

Track:

- Top competitors
- Upload frequency
- Viral topics
- Common keywords
- Common title patterns

Output:

Competitor Report

Including:

- Opportunities
- Threats
- Topic Gaps

---

Report Engine

Endpoint:

/reports

Authentication:

None

Purpose:

External Cron Trigger

Response:

{
"success": true
}

Workflow:

1. Analyze latest 3 videos
2. Analyze channel growth
3. Generate report
4. Send report to Telegram

---

Report Content

Include:

- Views
- CTR
- Retention
- Growth
- Best Video
- Worst Video
- Competitor Insights
- Suggested Next Topic
- Suggested Title Style

---

Telegram Commands

/start

/help

/channel

/videos

/video

/growth

/retention

/ctr

/seo

/competitors

/report

/title

/description

/tags

/strategy

---

Logging

Store:

- Tool Calls
- Errors
- AI Outputs
- Executed Changes
- Telegram Requests
- Reports

---

Database

SQLite

Tables:

users

reports

tool_logs

execution_logs

memory

competitors

video_cache

channel_cache

---

Health Endpoint

GET

/health

Response:

{
"status":"ok"
}

---

Deployment

Platform:

Render Free Plan

Requirements:

- Dockerfile
- Render Blueprint
- Environment Variables

---

Future Features

- Trend Detection
- Revenue Prediction
- Viral Probability Score
- A/B Title Testing
- Multi Channel Support
- Web Dashboard
- AI Memory Expansion
- Thumbnail Analysis
- Thumbnail Generator

---

Success Criteria

Admin can:

- Analyze channel
- Analyze videos
- Analyze competitors
- Receive reports
- Receive recommendations
- Approve title changes
- Approve description changes
- Approve tag changes

through Telegram

without unauthorized access.