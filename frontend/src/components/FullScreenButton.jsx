import React, { useState, useEffect } from 'react';
import { useFullScreen } from '../utils/fullscreen';
import './FullScreenButton.css';

/**
 * Full Screen Button Component
 * ===========================
 * 
 * Provides UI controls for entering/exiting full screen mode
 * with visual feedback and accessibility features
 */
const FullScreenButton = ({ className = '', showLabel = true, position = 'top-right' }) => {
  const [isFullScreen, setIsFullScreen] = useState(false);
  const { toggleFullScreen, isInFullScreen, onFullScreenChange } = useFullScreen();

  useEffect(() => {
    // Set initial state
    setIsFullScreen(isInFullScreen());

    // Listen for fullscreen changes
    const handleFullScreenChange = (fullScreenState) => {
      setIsFullScreen(fullScreenState);
    };

    onFullScreenChange(handleFullScreenChange);

    return () => {
      // Cleanup if needed
    };
  }, [isInFullScreen, onFullScreenChange]);

  const handleToggleFullScreen = async () => {
    try {
      await toggleFullScreen();
    } catch (error) {
      console.error('Error toggling fullscreen:', error);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleToggleFullScreen();
    }
  };

  return (
    <div className={`fullscreen-button-container ${position} ${className}`}>
      <button
        className={`fullscreen-button ${isFullScreen ? 'active' : ''}`}
        onClick={handleToggleFullScreen}
        onKeyDown={handleKeyDown}
        aria-label={isFullScreen ? 'Exit full screen' : 'Enter full screen'}
        title={isFullScreen ? 'Exit full screen (Esc)' : 'Enter full screen (F11)'}
      >
        <div className="fullscreen-icon">
          {isFullScreen ? (
            // Exit fullscreen icon
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3" />
            </svg>
          ) : (
            // Enter fullscreen icon
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
            </svg>
          )}
        </div>
        {showLabel && (
          <span className="fullscreen-label">
            {isFullScreen ? 'Exit Fullscreen' : 'Fullscreen'}
          </span>
        )}
      </button>
      
      {/* Keyboard shortcut indicator */}
      <div className="keyboard-hint">
        <span className="shortcut-key">F11</span>
        <span className="shortcut-key">ESC</span>
      </div>
    </div>
  );
};

export default FullScreenButton;