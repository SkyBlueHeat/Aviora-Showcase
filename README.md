# Aviora — Career Management Platform

A full-stack career management platform designed to organize job applications, interviews, analytics, follow-ups, and career-planning workflows in one structured experience.

Aviora was designed and developed as an independent end-to-end software project with a focus on reusable architecture, workflow design, automated testing, accessibility, and performance.

---

## Overview

Job seekers often manage applications across multiple platforms, spreadsheets, notes, calendars, and messaging tools.

This creates a fragmented workflow where it becomes difficult to track:

- active applications
- interview stages
- recruiter conversations
- follow-up deadlines
- target companies
- salary comparisons
- career goals
- skill gaps
- application performance

Aviora brings these workflows together into a centralized career-management system.

---

## Core Features

### Application Management

Track job applications through an organized workflow with:

- application status
- priority
- company and role information
- interview stages
- follow-up tracking
- fit scoring
- application history

### Kanban Workflow

Manage applications visually across different stages of the hiring process.

The workflow is designed to make application status changes easy to understand and update.

### Career Dashboard

A centralized dashboard provides visibility into job-search activity and progress.

Key areas include:

- applications
- interviews
- offers
- response rate
- goals
- progress metrics
- activity trends

### Analytics & Statistics

Aviora includes analytical tools for understanding job-search performance.

Examples include:

- application trends
- interview conversion
- response rates
- salary comparisons
- activity statistics
- progress tracking

### Interview Preparation

Structured interview-preparation workflows help users organize practice sessions and review their responses.

The system supports:

- interview categories
- practice questions
- answer review
- structured feedback
- preparation history

### Recruiter CRM

Manage professional contacts and recruiting conversations in one place.

Features include:

- recruiter information
- follow-up scheduling
- contact history
- notes
- networking tracking

### Resume & Job Description Analysis

Aviora includes tools for evaluating resumes and job descriptions before applying.

#### Resume Analysis

Supports:

- `.pdf`
- `.docx`
- `.txt`

Analysis can identify:

- keyword gaps
- weak action verbs
- formatting concerns
- job-description alignment
- improvement opportunities

#### Job Description Analysis

Job descriptions can be analyzed for:

- seniority level
- required skills
- preferred skills
- role requirements
- salary signals
- potential red flags
- potential green flags
- profile fit

### Salary & Offer Comparison

Compare opportunities using structured compensation data.

Includes:

- salary comparison
- total compensation analysis
- multiple-offer comparison
- weighted decision criteria

### Goals & Planning

Career-search planning tools include:

- daily goals
- weekly goals
- application tracking
- progress monitoring
- streak tracking
- weekly planning

### Reporting & Export

Career data can be exported into multiple formats for reporting or backup.

Supported workflows include:

- CSV export
- JSON export
- HTML export
- PDF reporting
- chart generation
- automated summaries
- backup workflows

---

## Engineering Contributions

Aviora was independently designed and developed as an end-to-end software project.

Key engineering work includes:

- Designed reusable UI architecture with React and TypeScript
- Built structured application-management workflows
- Implemented Kanban-based state management
- Developed career analytics and reporting workflows
- Built resume and job-description analysis utilities
- Implemented interview-preparation workflows
- Created reusable career-planning and tracking tools
- Added automated testing with Playwright and Vitest
- Implemented accessibility-conscious UI states
- Performed performance profiling and optimization
- Built supporting Python utilities and desktop workflows
- Designed export, reporting, and backup functionality

---

## Tech Stack

### Frontend

- React
- TypeScript
- JavaScript

### Application & Utilities

- Python
- PyWebView

### Testing

- Playwright
- Vitest

### Development

- Git
- GitHub
- Vite

---

## Performance

Performance was measured across multiple geographic regions.

| Metric | Result |
|---|---:|
| Mobile Lighthouse Performance | **94–98** |
| Largest Contentful Paint | **1.9–2.3s** |
| Total Blocking Time | **26–98ms** |
| Test Regions | **6** |

Performance work included:

- component optimization
- efficient state management
- asset optimization
- responsive loading behavior
- rendering improvements
- layout stability
- runtime performance analysis

---

## Testing & Quality

Aviora includes automated testing across important application workflows.

### Playwright

Used for end-to-end validation of user-facing workflows.

### Vitest

Used for application logic and component-level testing.

Quality work also includes:

- accessibility-conscious UI states
- responsive behavior
- browser compatibility
- performance profiling
- workflow validation

---

## Application Architecture

Aviora separates major responsibilities into reusable application layers.

```text
User Interface
      │
      ▼
React + TypeScript
      │
      ▼
Application Workflows
      │
      ├── Application Tracking
      ├── Kanban Management
      ├── Interview Preparation
      ├── Analytics
      ├── Career Planning
      └── Reporting
      │
      ▼
Python Utilities / PyWebView
      │
      ▼
Data Processing & Export
