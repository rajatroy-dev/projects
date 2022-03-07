/**
 * A custom class for throwing http specific error.
 */
class HttpError extends Error {
  code: number;

  /**
 * HttpError constructor.
 * @param {string} message A custom error message to be sent to user.
 * @param {int} code The error code.
 */
  constructor(message: string, code: number) {
    super(message);
    this.code = code;
  }
}

export default HttpError;
