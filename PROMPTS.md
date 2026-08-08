# PROMPTS.md

# AI Interview Agent — Vibe Coding Prompts

## Project

AI Interview Agent is an AI-powered technical interview platform that generates interview questions, evaluates candidate answers, provides scores, and displays answer keys.

## Main Development Prompts

### 1. Project Setup

Build an AI Interview Agent with a React/Vite frontend and FastAPI backend.

Requirements:

* React + Vite frontend
* FastAPI backend
* AI-generated interview questions
* Candidate information
* Technical interview flow
* Score calculation
* Answer evaluation
* Answer key
* Interactive UI
* Emojis and animations

### 2. Interview Questions

Create an interview system that generates technical questions based on the candidate profile, curriculum, and selected interview topic.

Questions should be displayed clearly one at a time with navigation controls.

### 3. Candidate Data

Use `candidates.json` to provide candidate information and `curriculum.json` to provide curriculum/topic information.

### 4. Interview Evaluation

Evaluate the candidate's answer and provide:

* Score
* Correct answer
* Explanation
* Feedback
* Final interview result

### 5. Frontend UI

Create a modern and engaging interview interface using React and Vite.

Include:

* Emojis
* Animations
* Progress indicators
* Question cards
* Answer area
* Score display
* Answer key
* Final result screen

### 6. Backend

Create a FastAPI backend that handles interview-related API requests and communicates with the AI service.

### 7. Deployment

Deploy the FastAPI backend on Render and deploy the React/Vite frontend on Vercel.

The frontend API base URL should point to the deployed Render backend.

## Deployment Architecture

```text
React + Vite Frontend
        |
        v
      Vercel
        |
        | API Requests
        v
   FastAPI Backend
        |
        v
      Render
        |
        v
       Gemini
```

## Final Verification

The deployed application should allow a user to:

1. Start an interview
2. View AI-generated questions
3. Submit answers
4. Receive evaluation
5. View scores
6. View answer keys
7. View feedback
8. Complete the interview
9. View the final result
