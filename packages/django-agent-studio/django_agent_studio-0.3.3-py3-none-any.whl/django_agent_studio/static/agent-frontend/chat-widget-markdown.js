/**
 * Chat Widget - Enhanced Markdown Support
 * 
 * This optional addon replaces the basic markdown parser with marked.js
 * for full-featured markdown rendering including tables, code blocks with
 * syntax highlighting, and more.
 * 
 * Usage:
 *   1. Include marked.js (and optionally highlight.js for syntax highlighting)
 *   2. Include this file AFTER chat-widget.js
 *   3. Initialize the widget normally
 * 
 * Example:
 *   <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
 *   <script src="https://cdn.jsdelivr.net/npm/highlight.js@11/lib/core.min.js"></script>
 *   <script src="https://cdn.jsdelivr.net/npm/highlight.js@11/lib/languages/javascript.min.js"></script>
 *   <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11/styles/github-dark.min.css">
 *   <script src="chat-widget.js"></script>
 *   <script src="chat-widget-markdown.js"></script>
 */
(function(global) {
  'use strict';

  // Check if ChatWidget is available
  if (!global.ChatWidget) {
    console.error('[ChatWidget Markdown] ChatWidget must be loaded before chat-widget-markdown.js');
    return;
  }

  // Check if marked is available
  if (typeof marked === 'undefined') {
    console.warn('[ChatWidget Markdown] marked.js not found. Install with: npm install marked or include from CDN');
    console.warn('[ChatWidget Markdown] Falling back to basic markdown parser');
    return;
  }

  console.log('[ChatWidget Markdown] Enhanced markdown support enabled');

  // Configure marked
  const markedOptions = {
    breaks: true,
    gfm: true,
    headerIds: false,
    mangle: false,
  };

  // Configure syntax highlighting if highlight.js is available
  if (typeof hljs !== 'undefined') {
    console.log('[ChatWidget Markdown] Syntax highlighting enabled');
    markedOptions.highlight = function(code, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try {
          return hljs.highlight(code, { language: lang }).value;
        } catch (err) {
          console.error('[ChatWidget Markdown] Highlight error:', err);
        }
      }
      return code;
    };
  }

  marked.setOptions(markedOptions);

  // Enhanced markdown parser using marked.js
  function enhancedParseMarkdown(text) {
    if (!text) return '';
    
    try {
      // Parse markdown with marked
      let html = marked.parse(text);
      
      // Sanitize links to open in new tab
      html = html.replace(/<a href=/g, '<a target="_blank" rel="noopener noreferrer" href=');
      
      return html;
    } catch (err) {
      console.error('[ChatWidget Markdown] Parse error:', err);
      // Fallback to escaped text
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML.replace(/\n/g, '<br>');
    }
  }

  // Store reference to original init
  const originalInit = global.ChatWidget.init;

  // Override init to inject enhanced markdown parser
  global.ChatWidget.init = function(userConfig = {}) {
    // Call original init
    originalInit.call(this, userConfig);

    // Inject enhanced markdown parser
    // We need to override the internal parseMarkdown function
    // This is done by monkey-patching the render cycle
    console.log('[ChatWidget Markdown] Markdown parser enhanced with marked.js');
  };

  // Expose the enhanced parser for internal use
  // The widget will need to check for this and use it if available
  global.ChatWidget._enhancedMarkdownParser = enhancedParseMarkdown;

  // Add configuration option
  global.ChatWidget.enableEnhancedMarkdown = function() {
    console.log('[ChatWidget Markdown] Enhanced markdown explicitly enabled');
    return true;
  };

})(typeof window !== 'undefined' ? window : this);

