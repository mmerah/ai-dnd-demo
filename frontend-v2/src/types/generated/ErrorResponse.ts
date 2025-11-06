/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = 'error';
export type Message = string;

/**
 * Response for errors.
 */
export interface ErrorResponse {
  type?: Type;
  message: Message;
}
