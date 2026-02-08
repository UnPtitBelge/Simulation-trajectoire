(function () {
  // Set initial Bootstrap theme to light before Dash renders
  try {
    document.documentElement.setAttribute('data-bs-theme', 'light');
  } catch (e) {
    // Silently ignore in environments where document might be unavailable
  }
})();
