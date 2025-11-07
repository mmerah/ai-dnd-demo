/**
 * Simple markdown renderer for chat messages
 * Supports: **bold**, *italic*, `code`, [links](url), headers, lists, and line breaks
 */

/**
 * Converts markdown text to HTML with proper escaping
 * Returns empty string if text is null/undefined (fail-safe)
 */
export function renderMarkdown(text: string | null | undefined): string {
  // Fail-safe: return empty string if text is null/undefined
  if (text == null) {
    console.warn('[renderMarkdown] Received null/undefined text, returning empty string');
    return '';
  }

  // Escape HTML to prevent XSS
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');

  // Convert markdown to HTML (in order of precedence)

  // Code blocks (```code```)
  html = html.replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>');

  // Inline code (`code`)
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Bold (**text** or __text__) - use non-greedy matching
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');

  // Italic (*text* or _text_) - use non-greedy matching
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  html = html.replace(/_(.+?)_/g, '<em>$1</em>');

  // Headers (### Header, ## Header, # Header)
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h4>$1</h4>');
  html = html.replace(/^# (.+)$/gm, '<h5>$1</h5>');

  // Lists (- item or * item)
  html = html.replace(/^[*-] (.+)$/gm, '<li>$1</li>');
  // Wrap consecutive <li> elements in <ul>
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');

  // Links [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

  // Line breaks (two newlines = paragraph, single newline = br)
  html = html.replace(/\n\n/g, '</p><p>');
  html = html.replace(/\n/g, '<br>');

  // Wrap in paragraph if not already wrapped
  if (!html.startsWith('<p>')) {
    html = '<p>' + html + '</p>';
  }

  return html;
}

/**
 * Safely sets innerHTML with rendered markdown
 * Handles null/undefined gracefully
 */
export function setMarkdownContent(element: HTMLElement, markdown: string | null | undefined): void {
  element.innerHTML = renderMarkdown(markdown);
}
