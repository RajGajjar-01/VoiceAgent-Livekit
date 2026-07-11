**Hiring Task: Python Automation Developer**

Voice-Driven AI Agent with Google Authentication

# 1\. Objective

The goal of this task is to evaluate your ability to build a small but complete, production-style application end to end. You will build a web application with Google-based authentication and a real-time voice assistant powered by LiveKit. The assistant should accept spoken input from the user, process the request through a backend AI agent, perform simple actions (such as booking a calendar event or managing tasks), and respond back to the user in voice.

# 2\. Task 1: Authentication System (Login with Google)

Build a user authentication system for the application with the following requirements:

* Users must be able to sign up and log in using their Google account (Google OAuth 2.0 / “Sign in with Google”).

* On successful login, create and persist a user session (JWT or session-based, your choice).

* Store basic user profile details (name, email, profile picture) in a database.

* Protect the voice assistant feature so that only authenticated users can access it.

* Handle logout and basic error states (denied consent, expired session, etc.).

# 3\. Task 2: Voice-Based AI Agent (LiveKit)

Using the open-source LiveKit stack (LiveKit server and the LiveKit Agents framework for Python), build a real-time voice assistant with the following flow:

## 3.1 Voice Input

* The user speaks a question or command through the browser (microphone input streamed via LiveKit).

* Speech is converted to text using an STT (speech-to-text) pipeline of your choice.

## 3.2 Backend Agent

* A Python-based agent runs in the backend and receives the transcribed user request.

* The agent understands the request and either answers the question or takes an action.

* Supported actions (minimum):

  * Booking / creating a calendar event (e.g., “Book a meeting tomorrow at 4 PM”).

  * Simple task management (e.g., adding a task or reminder to a list).

  * Small utility actions of your choice are a plus (e.g., checking today’s schedule).

## 3.3 Voice Output

* The agent’s response must be converted back to speech (TTS) and played to the user in real time through LiveKit.

* The interaction should feel conversational: the user asks by voice, the agent replies by voice.

# 4\. Suggested Tech Stack

You are free to choose your stack, but the following is recommended:

* **Backend:** Python (FastAPI / Flask / Django) for the backend.

* **Real-time voice:** LiveKit open-source server \+ LiveKit Agents (Python SDK).

* **STT / TTS:** Any STT/TTS provider or open-source models (e.g., Whisper, Deepgram, ElevenLabs, etc.).

* **LLM / Agent:** Any LLM of your choice for understanding requests and generating responses.

* **Auth & Calendar:** Google OAuth 2.0 for login; Google Calendar API (or a local mock) for event booking.

* **Frontend:** Any simple frontend (React, Next.js, or plain HTML/JS) that supports mic access.

# 5\. Deliverables

* A working end-to-end application (hosted demo link preferred; local setup acceptable).

* Complete source code in a Git repository (GitHub/GitLab) with clear commit history.

* A README with setup instructions, architecture overview, and environment variables required.

* A short screen recording (3–5 minutes) demonstrating: Google login, a voice question with a voice answer, and at least one voice-driven action (e.g., calendar event booking).

# 6\. Evaluation Criteria

* End-to-end completeness: login → voice input → agent → action/answer → voice output.

* Correct and secure implementation of Google authentication.

* Quality of the LiveKit integration and real-time voice experience (latency, reliability).

* Code quality, structure, and documentation.

* Handling of edge cases and errors (unclear speech, failed actions, unauthorized access).

# 7\. Timeline

| Duration | 3 days (end to end) |
| :---- | :---- |
| **Day 1** | Project setup, Google authentication, and basic app structure. |
| **Day 2** | LiveKit integration: voice input (STT), backend agent, and voice output (TTS). |
| **Day 3** | Agent actions (calendar booking, tasks), testing, polish, demo recording, and submission. |

*Note: The suggested day-wise split is indicative only. The hard requirement is completion of the full end-to-end task within 3 days of receiving it.*

# 8\. Submission

Share the repository link, demo link (if hosted), and the demo video within the 3-day deadline. If anything is unclear, feel free to ask questions before starting — asking good clarifying questions is also part of the evaluation. 