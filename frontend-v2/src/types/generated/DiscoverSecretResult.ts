/* AUTO-GENERATED FROM BACKEND - DO NOT EDIT */

export type Type = string;
export type SecretId = string;
export type Description = string;
export type Message = string;

export interface DiscoverSecretResult {
  type?: Type;
  secret_id: SecretId;
  description: Description;
  message: Message;
}
