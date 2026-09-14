// A single document-level keydown listener for the workspace keyboard shortcuts
// (fair_turn/app/components/keyboard.py). The keys it reacts to arrive in `data`, so this
// file carries no key literal of its own beyond the typing-target and modifier guards.
// Bound once per page: a flag on `window` survives this component remounting on a rerun,
// so the listener is never doubled.

const BOUND_FLAG = "__ftKeyboardBound";

function isTypingTarget(el) {
  if (!el) return false;
  const tag = el.tagName ? el.tagName.toLowerCase() : "";
  return tag === "input" || tag === "textarea" || tag === "select" || !!el.isContentEditable;
}

export default async function (component) {
  const { data, setTriggerValue } = component;
  const keys = new Set((data.keys || []).map((k) => String(k).toLowerCase()));
  if (window[BOUND_FLAG]) return;
  window[BOUND_FLAG] = true;
  let nonce = 0;

  document.addEventListener("keydown", (event) => {
    if (event.ctrlKey || event.altKey || event.metaKey) return;
    if (isTypingTarget(event.target) || isTypingTarget(document.activeElement)) return;
    const key = event.key.toLowerCase();
    if (!keys.has(key)) return;
    event.preventDefault();
    nonce += 1;
    setTriggerValue("pressed", { key, nonce });
  });
}
