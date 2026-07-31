/* confirm.js — "are you sure?" for destructive forms, without inline script.
 *
 * The console's Delete button carried onsubmit="return confirm(...)". An inline
 * event handler is inline script: the app-plane CSP is `script-src 'self'` with
 * no 'unsafe-inline', so the browser drops it and the form submits straight
 * through. The guard did not warn, error, or degrade — it simply stopped
 * existing, on the one control that destroys a teacher's question set.
 *
 * Delegated from the document so it covers forms rendered after load too, and
 * generic on purpose: any form that wants the prompt declares
 * data-confirm="…message…" and gets it.
 */
document.addEventListener("submit", (ev) => {
  const form = ev.target;
  if (!(form instanceof HTMLFormElement)) return;
  const message = form.dataset.confirm;
  if (message && !window.confirm(message)) {
    ev.preventDefault();
  }
});
