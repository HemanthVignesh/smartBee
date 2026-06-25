/**
 * Thrown when the backend responds with HTTP 429 Too Many Requests.
 * Consumers can check `instanceof RateLimitError` and show a specific UI
 * (e.g. a countdown toast) instead of a generic error message.
 */
export class RateLimitError extends Error {
  public readonly retryAfterSeconds: number;

  constructor(message: string, retryAfterSeconds = 60) {
    super(message);
    this.name = 'RateLimitError';
    this.retryAfterSeconds = retryAfterSeconds;
  }
}
