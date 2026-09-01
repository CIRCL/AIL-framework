import DOMPurify from 'dompurify'
import { marked } from 'marked'


// Only retain the non-interactive elements that Marked emits for formatting.
// Raw HTML, controls, links, media, embedded content, and styling attributes
// are removed by the allowlist rather than relying on an ever-growing blocklist.
const sanitizationOptions = {
  ALLOWED_TAGS: [
    'p', 'br', 'hr',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'pre', 'code',
    'ul', 'ol', 'li',
    'strong', 'em', 'del',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
  ],
  ALLOWED_ATTR: [],
  ALLOW_ARIA_ATTR: false,
  ALLOW_DATA_ATTR: false,
}

function createMarkdownRenderer(element, options={}) {
  const content = options.content ?? element.textContent
  // Model-generated descriptions are untrusted. Always sanitize Marked's HTML
  // with the strict allowlist before inserting it into the page.
  element.innerHTML = DOMPurify.sanitize(marked.parse(content), sanitizationOptions)
  element.dataset.markdownRendered = 'true'
  return element
}

function renderMarkdownElements(root=document) {
  return Array.from(root.querySelectorAll('.ail-markdown:not([data-markdown-rendered])'), (element) => {
    return createMarkdownRenderer(element)
  })
}

export { createMarkdownRenderer, renderMarkdownElements }
