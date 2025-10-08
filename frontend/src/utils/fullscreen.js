/**
 * Full Screen Utility Functions
 * =============================
 * 
 * Comprehensive full screen management for the AI Coordination Agent
 * Includes browser fullscreen API, responsive handling, and UI optimizations
 */

export class FullScreenManager {
  constructor() {
    this.isFullScreen = false;
    this.callbacks = [];
    this.init();
  }

  init() {
    // Listen for fullscreen changes
    document.addEventListener('fullscreenchange', this.handleFullScreenChange.bind(this));
    document.addEventListener('webkitfullscreenchange', this.handleFullScreenChange.bind(this));
    document.addEventListener('mozfullscreenchange', this.handleFullScreenChange.bind(this));
    document.addEventListener('MSFullscreenChange', this.handleFullScreenChange.bind(this));

    // Listen for escape key
    document.addEventListener('keydown', this.handleKeyPress.bind(this));

    // Handle window resize for responsive full screen
    window.addEventListener('resize', this.handleResize.bind(this));
  }

  /**
   * Enter full screen mode
   */
  async enterFullScreen(element = document.documentElement) {
    try {
      if (element.requestFullscreen) {
        await element.requestFullscreen();
      } else if (element.webkitRequestFullscreen) {
        await element.webkitRequestFullscreen();
      } else if (element.mozRequestFullScreen) {
        await element.mozRequestFullScreen();
      } else if (element.msRequestFullscreen) {
        await element.msRequestFullscreen();
      }
      
      this.optimizeForFullScreen();
      return true;
    } catch (error) {
      console.warn('Could not enter fullscreen:', error);
      this.simulateFullScreen();
      return false;
    }
  }

  /**
   * Exit full screen mode
   */
  async exitFullScreen() {
    try {
      if (document.exitFullscreen) {
        await document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        await document.webkitExitFullscreen();
      } else if (document.mozCancelFullScreen) {
        await document.mozCancelFullScreen();
      } else if (document.msExitFullscreen) {
        await document.msExitFullscreen();
      }
      
      this.restoreFromFullScreen();
      return true;
    } catch (error) {
      console.warn('Could not exit fullscreen:', error);
      this.exitSimulatedFullScreen();
      return false;
    }
  }

  /**
   * Toggle full screen mode
   */
  async toggleFullScreen(element) {
    if (this.isInFullScreen()) {
      return await this.exitFullScreen();
    } else {
      return await this.enterFullScreen(element);
    }
  }

  /**
   * Check if currently in full screen
   */
  isInFullScreen() {
    return !!(
      document.fullscreenElement ||
      document.webkitFullscreenElement ||
      document.mozFullScreenElement ||
      document.msFullscreenElement ||
      this.isFullScreen
    );
  }

  /**
   * Simulate full screen when native API is not available
   */
  simulateFullScreen() {
    const appContainer = document.getElementById('root');
    if (appContainer) {
      appContainer.classList.add('fullscreen-simulated');
      document.body.classList.add('no-scroll');
      this.isFullScreen = true;
      this.optimizeForFullScreen();
    }
  }

  /**
   * Exit simulated full screen
   */
  exitSimulatedFullScreen() {
    const appContainer = document.getElementById('root');
    if (appContainer) {
      appContainer.classList.remove('fullscreen-simulated');
      document.body.classList.remove('no-scroll');
      this.isFullScreen = false;
      this.restoreFromFullScreen();
    }
  }

  /**
   * Optimize UI for full screen experience
   */
  optimizeForFullScreen() {
    // Hide browser UI elements
    document.body.classList.add('fullscreen-active');
    
    // Add full screen styles
    const style = document.createElement('style');
    style.id = 'fullscreen-styles';
    style.textContent = `
      .fullscreen-simulated {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        z-index: 9999 !important;
        background: #1a1a1a !important;
      }
      
      .fullscreen-active .navbar {
        backdrop-filter: blur(20px) !important;
        background: rgba(26, 26, 26, 0.8) !important;
      }
      
      .fullscreen-active .dashboard-card {
        backdrop-filter: blur(15px) !important;
      }
    `;
    
    if (!document.getElementById('fullscreen-styles')) {
      document.head.appendChild(style);
    }

    // Trigger callbacks
    this.callbacks.forEach(callback => callback(true));
  }

  /**
   * Restore UI from full screen
   */
  restoreFromFullScreen() {
    document.body.classList.remove('fullscreen-active');
    
    // Remove full screen styles
    const style = document.getElementById('fullscreen-styles');
    if (style) {
      style.remove();
    }

    // Trigger callbacks
    this.callbacks.forEach(callback => callback(false));
  }

  /**
   * Handle full screen change events
   */
  handleFullScreenChange() {
    const isFullScreen = this.isInFullScreen();
    
    if (isFullScreen) {
      this.optimizeForFullScreen();
    } else {
      this.restoreFromFullScreen();
    }
  }

  /**
   * Handle key press events (ESC to exit fullscreen)
   */
  handleKeyPress(event) {
    if (event.key === 'Escape' && this.isInFullScreen()) {
      this.exitFullScreen();
    }
    
    // F11 for fullscreen toggle
    if (event.key === 'F11') {
      event.preventDefault();
      this.toggleFullScreen();
    }
  }

  /**
   * Handle window resize for responsive full screen
   */
  handleResize() {
    if (this.isInFullScreen()) {
      // Update viewport height for mobile browsers
      const vh = window.innerHeight * 0.01;
      document.documentElement.style.setProperty('--vh', `${vh}px`);
    }
  }

  /**
   * Add callback for full screen state changes
   */
  onFullScreenChange(callback) {
    this.callbacks.push(callback);
  }

  /**
   * Remove callback
   */
  removeFullScreenChangeListener(callback) {
    const index = this.callbacks.indexOf(callback);
    if (index > -1) {
      this.callbacks.splice(index, 1);
    }
  }

  /**
   * Get current screen dimensions
   */
  getScreenDimensions() {
    return {
      width: window.innerWidth,
      height: window.innerHeight,
      availWidth: screen.availWidth,
      availHeight: screen.availHeight,
      devicePixelRatio: window.devicePixelRatio || 1
    };
  }

  /**
   * Optimize for different screen sizes
   */
  optimizeForScreenSize() {
    const dimensions = this.getScreenDimensions();
    
    // Add classes based on screen size
    document.body.classList.remove('small-screen', 'medium-screen', 'large-screen');
    
    if (dimensions.width < 768) {
      document.body.classList.add('small-screen');
    } else if (dimensions.width < 1200) {
      document.body.classList.add('medium-screen');
    } else {
      document.body.classList.add('large-screen');
    }
  }
}

// Create and export singleton instance
export const fullScreenManager = new FullScreenManager();

// Export utility functions for React components
export const useFullScreen = () => {
  return {
    enterFullScreen: fullScreenManager.enterFullScreen.bind(fullScreenManager),
    exitFullScreen: fullScreenManager.exitFullScreen.bind(fullScreenManager),
    toggleFullScreen: fullScreenManager.toggleFullScreen.bind(fullScreenManager),
    isInFullScreen: fullScreenManager.isInFullScreen.bind(fullScreenManager),
    onFullScreenChange: fullScreenManager.onFullScreenChange.bind(fullScreenManager)
  };
};

export default fullScreenManager;