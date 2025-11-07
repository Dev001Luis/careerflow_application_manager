// app/static/js/ajax_swap.js
/**
 * Simple reusable async content swapper.
 *
 * Behavior:
 * - Intercept form submit and link/button clicks with data-ajax-target attribute.
 * - POST a form or GET a url and replace target DOM content with returned HTML fragment.
 *
 * HTML usage:
 *  <button data-ajax-target="#jobList" data-url="/some-route">Refresh</button>
 *  <form data-ajax-target="#jobList" action="/upload-linkedin" method="post" enctype="multipart/form-data">...</form>
 *
 * If server returns JSON with key "jobs_list_html", it will use that HTML to replace the target.
 */

document.addEventListener("submit", async (e) => {
  const formElement = e.target;
  if (!formElement.hasAttribute("data-ajax-target")) return;

  e.preventDefault();
  const ajaxTargetSelector = formElement.getAttribute("data-ajax-target");
  const formData = new FormData(formElement);
  const actionUrl = formElement.getAttribute("action") || window.location.pathname;

  try {
    const response = await fetch(actionUrl, { method: "POST", body: formData });
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      const json = await response.json();
      if (json.jobs_list_html) {
        const targetElement = document.querySelector(ajaxTargetSelector);
        if (targetElement) targetElement.innerHTML = json.jobs_list_html;
      }
      const messageElement = document.getElementById("uploadMessage");
      if (messageElement) messageElement.textContent = `Imported ${json.imported} jobs.`;
    } else {
      const html = await response.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      const newFragment = doc.querySelector(ajaxTargetSelector);
      const oldFragment = document.querySelector(ajaxTargetSelector);
      if (oldFragment && newFragment) oldFragment.replaceWith(newFragment);
    }
  } catch (err) {
    console.error("Async form submit failed:", err);
  }
});

document.addEventListener("click", async (e) => {
  const trigger = e.target.closest("[data-ajax-target][data-url]");
  if (!trigger) return;

  e.preventDefault();
  const ajaxTargetSelector = trigger.getAttribute("data-ajax-target");
  const urlToFetch = trigger.getAttribute("data-url");

  try {
    const response = await fetch(urlToFetch);
    const html = await response.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const newFragment = doc.querySelector(ajaxTargetSelector);
    const oldFragment = document.querySelector(ajaxTargetSelector);
    if (oldFragment && newFragment) oldFragment.replaceWith(newFragment);
  } catch (err) {
    console.error("Async click fetch failed:", err);
  }
});
