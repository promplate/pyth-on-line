export function needScroll(element?: HTMLElement, threshold = 200) {
  if (!element)
    return false;

  const offsetBottom = element.scrollHeight - element.clientHeight - element.scrollTop;

  return offsetBottom < threshold;
}

export function scrollToBottom(element?: HTMLElement, behavior: ScrollBehavior = "smooth") {
  if (!element)
    return;

  element.scrollTo({ top: element.scrollHeight, behavior });
}
