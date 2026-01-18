import React from 'react';
import './LoadingSpinner.css';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  message?: string;
  fullScreen?: boolean;
}

/**
 * Loading Spinner Component
 * Displays a loading indicator with optional message
 * Can be small (inline), medium (page), or large (full screen)
 */
const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  message,
  fullScreen = false,
}) => {
  return (
    <div className={`loading-container ${fullScreen ? 'fullscreen' : ''}`}>
      <div className={`spinner ${size}`}>
        <div className="spinner-dot"></div>
        <div className="spinner-dot"></div>
        <div className="spinner-dot"></div>
      </div>
      {message && <p className="loading-message">{message}</p>}
    </div>
  );
};

export default LoadingSpinner;
