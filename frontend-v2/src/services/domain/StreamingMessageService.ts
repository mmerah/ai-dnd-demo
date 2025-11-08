/**
 * Service responsible for managing streaming message state.
 * Extracted from GameInterfaceScreen to follow Single Responsibility Principle.
 *
 * Manages the lifecycle of streaming messages:
 * - Starting a new stream
 * - Appending deltas to the buffer
 * - Ending a stream and resetting state
 */

/**
 * Streaming message state
 */
export interface StreamState {
  /** Accumulated message content */
  buffer: string;
  /** Message key for updating in ChatPanel */
  messageKey: string | null;
}

/**
 * Service for managing streaming message state
 */
export class StreamingMessageService {
  private streams: Map<string, StreamState> = new Map();

  /**
   * Starts a new streaming message
   * @param streamId - Unique identifier for this stream
   * @returns The stream ID for subsequent operations
   */
  startStream(streamId: string): string {
    this.streams.set(streamId, {
      buffer: '',
      messageKey: null,
    });

    return streamId;
  }

  /**
   * Appends a delta to the stream buffer
   * @param streamId - Stream identifier
   * @param delta - New content to append
   * @returns Updated buffer content
   */
  appendDelta(streamId: string, delta: string): string {
    const stream = this.streams.get(streamId);

    if (!stream) {
      throw new Error(`Stream not found: ${streamId}`);
    }

    stream.buffer += delta;
    return stream.buffer;
  }

  /**
   * Sets the message key for a stream (used after creating the message in chat)
   * @param streamId - Stream identifier
   * @param messageKey - Chat message key from ChatPanel
   */
  setMessageKey(streamId: string, messageKey: string): void {
    const stream = this.streams.get(streamId);

    if (!stream) {
      throw new Error(`Stream not found: ${streamId}`);
    }

    stream.messageKey = messageKey;
  }

  /**
   * Gets the current buffer content for a stream
   * @param streamId - Stream identifier
   * @returns Current buffer content
   */
  getBuffer(streamId: string): string {
    const stream = this.streams.get(streamId);

    if (!stream) {
      throw new Error(`Stream not found: ${streamId}`);
    }

    return stream.buffer;
  }

  /**
   * Gets the message key for a stream
   * @param streamId - Stream identifier
   * @returns Message key or null if not set
   */
  getMessageKey(streamId: string): string | null {
    const stream = this.streams.get(streamId);

    if (!stream) {
      throw new Error(`Stream not found: ${streamId}`);
    }

    return stream.messageKey;
  }

  /**
   * Checks if a stream exists
   * @param streamId - Stream identifier
   * @returns True if stream exists
   */
  hasStream(streamId: string): boolean {
    return this.streams.has(streamId);
  }

  /**
   * Ends a stream and removes it from state
   * @param streamId - Stream identifier
   */
  endStream(streamId: string): void {
    this.streams.delete(streamId);
  }

  /**
   * Gets the state for a stream (for testing/debugging)
   * @param streamId - Stream identifier
   * @returns Stream state or undefined if not found
   */
  getStreamState(streamId: string): StreamState | undefined {
    return this.streams.get(streamId);
  }

  /**
   * Gets the number of active streams
   * @returns Count of active streams
   */
  getActiveStreamCount(): number {
    return this.streams.size;
  }

  /**
   * Ends all active streams (useful for cleanup)
   */
  clearAllStreams(): void {
    this.streams.clear();
  }
}
