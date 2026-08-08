import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:8000";

const TOTAL_QUESTIONS = 8;

function App() {
  const [sessionId, setSessionId] = useState(() => {
    return localStorage.getItem("interviewSessionId") || "";
  });

  const [candidate, setCandidate] = useState({
    id: "CAND-001",
    name: "Candidate",
  });

  const [question, setQuestion] = useState(null);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");

  const [result, setResult] = useState(null);

  const textareaRef = useRef(null);

  /*
   * ---------------------------------------------------------
   * START INTERVIEW
   * ---------------------------------------------------------
   */
  const startInterview = async () => {
    setStarting(true);
    setLoading(true);
    setError("");
    setResult(null);
    setAnswer("");
    setQuestion(null);

    const newSessionId =
      "session-" + Date.now() + "-" + Math.random().toString(36).slice(2, 8);

    try {
      const response = await fetch(`${API_BASE}/api/interview`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          sessionId: newSessionId,
          candidate: candidate,
          message: null,
        }),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `Server returned ${response.status}`);
      }

      const data = await response.json();

      localStorage.setItem("interviewSessionId", newSessionId);
      setSessionId(newSessionId);

      if (data.done) {
        setResult(data);
      } else {
        setQuestion(data);
      }
    } catch (err) {
      console.error(err);
      setError(
        "Could not start the interview. Make sure your FastAPI backend is running on port 8000."
      );
    } finally {
      setLoading(false);
      setStarting(false);
    }
  };

  /*
   * ---------------------------------------------------------
   * SUBMIT ANSWER
   * ---------------------------------------------------------
   */
  const submitAnswer = async () => {
    const trimmedAnswer = answer.trim();

    if (!trimmedAnswer) {
      setError("Please enter an answer before submitting.");
      textareaRef.current?.focus();
      return;
    }

    if (!sessionId) {
      setError("Interview session not found. Please start a new interview.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE}/api/interview`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          sessionId: sessionId,
          candidate: candidate,
          message: trimmedAnswer,
        }),
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `Server returned ${response.status}`);
      }

      const data = await response.json();

      setAnswer("");

      if (data.done) {
        /*
         * IMPORTANT:
         * The backend returns:
         *
         * score
         * feedback
         * strengths
         * areasToImprove
         * answerKey
         *
         * We store the complete object here.
         */
        setResult(data);
        setQuestion(null);
      } else {
        setQuestion(data);
      }
    } catch (err) {
      console.error(err);
      setError(
        "Could not submit your answer. Check that the backend is running and try again."
      );
    } finally {
      setLoading(false);
    }
  };

  /*
   * ---------------------------------------------------------
   * RESET INTERVIEW
   * ---------------------------------------------------------
   */
  const resetInterview = async () => {
    if (sessionId) {
      try {
        await fetch(`${API_BASE}/api/interview/${sessionId}`, {
          method: "DELETE",
        });
      } catch (err) {
        console.warn("Could not delete old session:", err);
      }
    }

    localStorage.removeItem("interviewSessionId");

    setSessionId("");
    setQuestion(null);
    setAnswer("");
    setResult(null);
    setError("");
  };

  /*
   * ---------------------------------------------------------
   * ENTER KEY SUBMISSION
   * ---------------------------------------------------------
   */
  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();

      if (!loading) {
        submitAnswer();
      }
    }
  };

  /*
   * ---------------------------------------------------------
   * CHARACTER COUNT
   * ---------------------------------------------------------
   */
  const characterCount = answer.length;

  /*
   * ---------------------------------------------------------
   * PROGRESS
   * ---------------------------------------------------------
   */
  const currentQuestionNumber = question?.questionNumber || 1;

  const progress = question
    ? Math.min(
        100,
        ((currentQuestionNumber - 1) / TOTAL_QUESTIONS) * 100
      )
    : result
    ? 100
    : 0;

  /*
   * ---------------------------------------------------------
   * AUTO FOCUS
   * ---------------------------------------------------------
   */
  useEffect(() => {
    if (question && !loading) {
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 100);
    }
  }, [question, loading]);

  /*
   * =========================================================
   * WELCOME SCREEN
   * =========================================================
   */
  if (!question && !result) {
    return (
      <div className="app-shell">
        <header className="topbar">
          <div className="brand">
            <div className="brand-icon">AI</div>

            <div>
              <div className="brand-title">AI Interviewer</div>
              <div className="brand-subtitle">
                Technical Interview Agent
              </div>
            </div>
          </div>

          <div className="live-session">
            <span className="live-dot"></span>
            Ready
          </div>
        </header>

        <main className="main-content welcome-content">
          <section className="welcome-card">
            <div className="welcome-icon">AI</div>

            <div className="eyebrow">AI INTERVIEWER</div>

            <h1>Technical Interview</h1>

            <p className="welcome-description">
              Test your knowledge of AI engineering, RAG, vector databases,
              agents, MCP, production architecture, evaluation, and deployment.
            </p>

            <div className="candidate-box">
              <div>
                <span className="candidate-label">Candidate</span>
                <strong>{candidate.name}</strong>
              </div>

              <div>
                <span className="candidate-label">Questions</span>
                <strong>{TOTAL_QUESTIONS}</strong>
              </div>
            </div>

            {error && <div className="error-message">{error}</div>}

            <button
              className="primary-button large-button"
              onClick={startInterview}
              disabled={loading}
            >
              {starting ? "Starting Interview..." : "Start Interview →"}
            </button>

            <p className="hint-text">
              You can press Enter to submit each answer.
            </p>
          </section>
        </main>
      </div>
    );
  }

  /*
   * =========================================================
   * RESULT SCREEN
   * =========================================================
   */
  if (result) {
    const score = Number(result.score || 0);

    let scoreClass = "score-low";

    if (score >= 80) {
      scoreClass = "score-excellent";
    } else if (score >= 60) {
      scoreClass = "score-good";
    } else if (score >= 40) {
      scoreClass = "score-average";
    }

    return (
      <div className="app-shell">
        <header className="topbar">
          <div className="brand">
            <div className="brand-icon">AI</div>

            <div>
              <div className="brand-title">AI Interviewer</div>
              <div className="brand-subtitle">
                Technical Interview Agent
              </div>
            </div>
          </div>

          <div className="live-session completed-status">
            <span className="completed-dot"></span>
            Interview Completed
          </div>
        </header>

        <main className="main-content results-content">
          {/* HERO */}
          <section className="results-hero">
            <div className="celebration">🎉</div>

            <div className="eyebrow">INTERVIEW COMPLETE</div>

            <h1>Interview Results</h1>

            <p>
              Your technical interview has been evaluated.
            </p>
          </section>

          {/* SCORE */}
          <section className="result-grid">
            <div className="score-card">
              <div className="card-label">OVERALL SCORE</div>

              <div className={`score-circle ${scoreClass}`}>
                <div className="score-number">{score}</div>
                <div className="score-out-of">/ 100</div>
              </div>

              <div className="score-status">
                {score >= 80
                  ? "Excellent Performance"
                  : score >= 60
                  ? "Good Performance"
                  : score >= 40
                  ? "Needs Improvement"
                  : "Keep Practicing"}
              </div>
            </div>

            {/* FEEDBACK */}
            <div className="feedback-card">
              <div className="card-label">AI FEEDBACK</div>

              <h2>Overall Feedback</h2>

              <p className="feedback-text">
                {result.feedback ||
                  "No overall feedback was provided."}
              </p>

              <div className="feedback-columns">
                <div className="feedback-section">
                  <h3>
                    <span className="success-icon">✓</span>
                    Strengths
                  </h3>

                  {Array.isArray(result.strengths) &&
                  result.strengths.length > 0 ? (
                    <ul>
                      {result.strengths.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="muted">No strengths recorded.</p>
                  )}
                </div>

                <div className="feedback-section">
                  <h3>
                    <span className="warning-icon">!</span>
                    Areas to Improve
                  </h3>

                  {Array.isArray(result.areasToImprove) &&
                  result.areasToImprove.length > 0 ? (
                    <ul>
                      {result.areasToImprove.map((item, index) => (
                        <li key={index}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    <p className="muted">
                      No improvement areas recorded.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </section>

          {/* ANSWER KEY */}
          <section className="answer-key-section">
            <div className="section-heading">
              <div>
                <div className="eyebrow">DETAILED REVIEW</div>
                <h2>Answer Key</h2>
                <p>
                  Compare your answers with the expected technical answers.
                </p>
              </div>

              <div className="answer-count">
                {result.answerKey?.length || 0} Questions
              </div>
            </div>

            {Array.isArray(result.answerKey) &&
            result.answerKey.length > 0 ? (
              <div className="answer-list">
                {result.answerKey.map((item, index) => {
                  const questionScore = Number(
                    item.questionScore || 0
                  );

                  let questionScoreClass = "score-badge-low";

                  if (questionScore >= 80) {
                    questionScoreClass = "score-badge-high";
                  } else if (questionScore >= 60) {
                    questionScoreClass = "score-badge-good";
                  } else if (questionScore >= 40) {
                    questionScoreClass = "score-badge-medium";
                  }

                  return (
                    <article
                      className="answer-card"
                      key={`${item.questionNumber}-${index}`}
                    >
                      <div className="answer-card-header">
                        <div className="question-meta">
                          <span className="question-number">
                            Q{item.questionNumber}
                          </span>

                          <span className="topic-badge">
                            {item.topic}
                          </span>
                        </div>

                        <span
                          className={`question-score ${questionScoreClass}`}
                        >
                          {questionScore}/100
                        </span>
                      </div>

                      <div className="question-block">
                        <div className="block-label">
                          QUESTION
                        </div>

                        <p>{item.question}</p>
                      </div>

                      <div className="answer-comparison">
                        <div className="candidate-answer">
                          <div className="block-label">
                            YOUR ANSWER
                          </div>

                          <div className="answer-text">
                            {item.candidateAnswer ||
                              "No answer provided."}
                          </div>
                        </div>

                        <div className="expected-answer">
                          <div className="block-label">
                            EXPECTED ANSWER
                          </div>

                          <div className="answer-text">
                            {item.expectedAnswer ||
                              "No expected answer available."}
                          </div>
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            ) : (
              <div className="empty-answer-key">
                <div className="empty-icon">?</div>
                <h3>No answer key available</h3>
                <p>
                  The backend did not return detailed answer data.
                </p>
              </div>
            )}
          </section>

          {/* ACTIONS */}
          <section className="results-actions">
            <button
              className="primary-button"
              onClick={resetInterview}
            >
              Start New Interview
            </button>
          </section>
        </main>
      </div>
    );
  }

  /*
   * =========================================================
   * INTERVIEW SCREEN
   * =========================================================
   */
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">AI</div>

          <div>
            <div className="brand-title">AI Interviewer</div>
            <div className="brand-subtitle">
              Technical Interview Agent
            </div>
          </div>
        </div>

        <div className="live-session">
          <span className="live-dot"></span>
          Live Session
        </div>
      </header>

      <main className="main-content interview-content">
        {/* INTERVIEW HEADER */}
        <section className="interview-header">
          <div>
            <div className="eyebrow">AI INTERVIEWER</div>

            <h1>Technical Interview</h1>
          </div>

          <div className="question-counter">
            Question {question.questionNumber} of{" "}
            {question.totalQuestions || TOTAL_QUESTIONS}
          </div>
        </section>

        {/* PROGRESS */}
        <div className="progress-container">
          <div
            className="progress-bar"
            style={{ width: `${progress}%` }}
          ></div>
        </div>

        {/* QUESTION */}
        <section className="question-section">
          <div className="eyebrow">AI INTERVIEWER</div>

          <div className="topic-title">{question.topic}</div>

          <div className="question-card">
            {question.question}
          </div>
        </section>

        {/* ANSWER BOX */}
        <section className="answer-panel">
          <div className="answer-header">
            <label htmlFor="answer">Your Answer</label>

            <span>Press Enter to submit</span>
          </div>

          <div className="answer-row">
            <textarea
              ref={textareaRef}
              id="answer"
              value={answer}
              onChange={(event) => setAnswer(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your technical answer here..."
              disabled={loading}
              rows={5}
            />

            <button
              className="send-button"
              onClick={submitAnswer}
              disabled={loading || !answer.trim()}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Sending...
                </>
              ) : (
                <>
                  Send Answer <span>→</span>
                </>
              )}
            </button>
          </div>

          <div className="answer-footer">
            <span>Be specific and explain your reasoning.</span>

            <span>{characterCount} characters</span>
          </div>
        </section>

        {error && (
          <div className="error-message interview-error">
            {error}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;