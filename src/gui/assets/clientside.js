/**
 * Dash clientside functions
 *
 * This file defines clientside function namespaces used by Dash's clientside_callback,
 * preventing errors such as:
 *   "can't access property 'apply', dc[namespace][function_name] is undefined"
 *
 * Place this file under `assets/` so Dash automatically serves it.
 */

(function () {
  // Ensure the global dash_clientside object exists
  if (typeof window.dash_clientside !== "object" || window.dash_clientside === null) {
    window.dash_clientside = {};
  }

  // Provide a no_update sentinel if missing
  if (typeof window.dash_clientside.no_update === "undefined") {
    // Dash expects a special sentinel to indicate no property update on the client
    // Using a unique object instance as a stand-in is acceptable for clientside functions.
    window.dash_clientside.no_update = { __dash_no_update__: true };
  }

  /**
   * Namespace: theme
   * Functions to manage theme-related behaviors.
   */
  if (typeof window.dash_clientside.theme !== "object" || window.dash_clientside.theme === null) {
    window.dash_clientside.theme = {};
  }

  /**
   * Toggle Bootstrap color mode (light/dark) based on a switch value.
   * Args:
   *   switchOn (boolean): true -> light, false -> dark
   * Returns:
   *   window.dash_clientside.no_update
   */
  window.dash_clientside.theme.toggle_color_mode = function (switchOn) {
    try {
      var mode = switchOn ? "light" : "dark";
      document.documentElement.setAttribute("data-bs-theme", mode);
    } catch (e) {
      // Fail silently; do not break Dash updates
    }
    return window.dash_clientside.no_update;
  };

  /**
   * Namespace: navbar
   * Functions to control mobile navbar collapses.
   */
  if (typeof window.dash_clientside.navbar !== "object" || window.dash_clientside.navbar === null) {
    window.dash_clientside.navbar = {};
  }

  /**
   * Toggle collapse based on click count and current open state.
   * Args:
   *   nClicks (number | undefined): click counter from the toggler
   *   isOpen (boolean | undefined): current collapse state
   * Returns:
   *   boolean: next isOpen state
   */
  window.dash_clientside.navbar.toggle_collapse = function (nClicks, isOpen) {
    if (!nClicks) return !!isOpen;
    return !isOpen;
  };

  /**
   * Namespace: utils
   * General helpers, if needed by other clientside callbacks.
   */
  if (typeof window.dash_clientside.utils !== "object" || window.dash_clientside.utils === null) {
    window.dash_clientside.utils = {};
  }

  /**
   * Safely parse a float, falling back to default if value is null/undefined/NaN.
   * Args:
   *   value: any
   *   fallback: number
   * Returns:
   *   number
   */
  window.dash_clientside.utils.safeFloat = function (value, fallback) {
    if (value === null || value === undefined) return fallback;
    var n = Number.parseFloat(value);
    return Number.isNaN(n) ? fallback : n;
  };
})();
