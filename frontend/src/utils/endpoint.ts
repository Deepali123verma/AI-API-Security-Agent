export function splitEndpoint(endpoint?: string | null): {
  method: string | null
  path: string | null
} {
  if (!endpoint) {
    return { method: null, path: null }
  }
  const trimmed = endpoint.trim()
  const space = trimmed.indexOf(' ')
  if (space === -1) {
    return { method: null, path: trimmed }
  }
  return {
    method: trimmed.slice(0, space).toUpperCase(),
    path: trimmed.slice(space + 1),
  }
}
