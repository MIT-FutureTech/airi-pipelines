const DOC_PARAM = "doc";

export function getDocFromUrl(): string | null {
  return new URLSearchParams(window.location.search).get(DOC_PARAM);
}

export function setDocInUrl(readableId: string | null): void {
  const url = new URL(window.location.href);
  if (readableId === null) {
    url.searchParams.delete(DOC_PARAM);
  } else {
    url.searchParams.set(DOC_PARAM, readableId);
  }
  window.history.replaceState(null, "", url);
}
