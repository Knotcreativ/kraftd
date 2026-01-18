import React, { useState } from 'react';
import './ExportComplete.css';

interface ExportCompleteProps {
  exportWorkflowId: string;
  documentId: string;
  fileName: string;
  onFeedbackSubmitted: () => void;
  onNewConversion: () => void;
}

export const ExportComplete: React.FC<ExportCompleteProps> = ({
  exportWorkflowId,
  documentId,
  fileName,
  onFeedbackSubmitted,
  onNewConversion
}) => {
  const [feedbackText, setFeedbackText] = useState('');
  const [satisfactionRating, setSatisfactionRating] = useState(5);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmitFeedback = async () => {
    if (!feedbackText.trim()) {
      setError('Please enter some feedback before submitting.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/v1/exports/${exportWorkflowId}/feedback`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: JSON.stringify({
            feedback_text: feedbackText,
            satisfaction_rating: satisfactionRating,
            download_successful: true
          })
        }
      );

      if (response.ok) {
        setSubmitSuccess(true);
        onFeedbackSubmitted();
        
        // Auto-reset after 2 seconds
        setTimeout(() => {
          setSubmitSuccess(false);
          setFeedbackText('');
          setSatisfactionRating(5);
        }, 2000);
      } else {
        setError('Failed to submit feedback. Please try again.');
      }
    } catch (err) {
      setError('Error submitting feedback. Please try again.');
      console.error('Feedback submission error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="export-complete-container">
      {submitSuccess ? (
        <div className="feedback-success-screen">
          <div className="success-checkmark">✓</div>
          <h2>Thank You!</h2>
          <p>Your feedback has been submitted and will help us improve KraftdIntel.</p>
          <p className="feedback-impact">This feedback will be analyzed by our AI model to enhance future exports.</p>
        </div>
      ) : (
        <>
          <div className="download-complete-header">
            <div className="completion-icon">
              <svg viewBox="0 0 24 24" width="48" height="48" fill="#4caf50">
                <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
              </svg>
            </div>
            <h2>Download Completed!</h2>
            <p className="file-name">📄 {fileName}</p>
          </div>

          <div className="feedback-section">
            <h3>Help Us Improve</h3>
            <p className="feedback-subtitle">
              Your feedback helps our AI model learn and provide better results in the future.
            </p>

            {/* Satisfaction Rating */}
            <div className="rating-section">
              <label>How satisfied are you with this export?</label>
              <div className="star-rating">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    className={`star ${satisfactionRating >= star ? 'active' : ''}`}
                    onClick={() => setSatisfactionRating(star)}
                    title={`Rate ${star} star${star > 1 ? 's' : ''}`}
                  >
                    ★
                  </button>
                ))}
              </div>
              <div className="rating-label">
                {satisfactionRating === 5 && 'Excellent!'}
                {satisfactionRating === 4 && 'Good'}
                {satisfactionRating === 3 && 'Neutral'}
                {satisfactionRating === 2 && 'Could be better'}
                {satisfactionRating === 1 && 'Needs improvement'}
              </div>
            </div>

            {/* Feedback Text Area */}
            <div className="feedback-textarea-section">
              <label htmlFor="feedbackText">
                Your Feedback (Optional but helpful)
              </label>
              <textarea
                id="feedbackText"
                className="feedback-textarea"
                placeholder="Tell us what you think... What worked well? What could be improved? Any specific suggestions?"
                value={feedbackText}
                onChange={(e) => setFeedbackText(e.target.value)}
                maxLength={1000}
                rows={5}
              />
              <div className="char-count">
                {feedbackText.length} / 1000 characters
              </div>
            </div>

            {/* Error Message */}
            {error && <div className="error-message">{error}</div>}

            {/* Action Buttons */}
            <div className="action-buttons">
              <button
                className="submit-feedback-btn"
                onClick={handleSubmitFeedback}
                disabled={isSubmitting || !feedbackText.trim()}
              >
                {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
              </button>
              <button
                className="new-conversion-btn"
                onClick={onNewConversion}
              >
                + New Conversion
              </button>
            </div>

            {/* Feedback Benefits */}
            <div className="feedback-benefits">
              <h4>Why share feedback?</h4>
              <ul>
                <li>✓ Help improve AI accuracy</li>
                <li>✓ Shape future features</li>
                <li>✓ Get better results next time</li>
                <li>✓ Support product development</li>
              </ul>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
