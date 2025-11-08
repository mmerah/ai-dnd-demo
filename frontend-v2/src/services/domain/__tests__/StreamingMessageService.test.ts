import { describe, it, expect } from 'vitest';
import { StreamingMessageService } from '../StreamingMessageService';

describe('StreamingMessageService', () => {
  describe('startStream', () => {
    it('should create a new stream with empty buffer', () => {
      const service = new StreamingMessageService();

      const streamId = service.startStream('stream-1');

      expect(streamId).toBe('stream-1');
      expect(service.hasStream('stream-1')).toBe(true);
      expect(service.getBuffer('stream-1')).toBe('');
      expect(service.getMessageKey('stream-1')).toBeNull();
    });

    it('should allow multiple streams', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      service.startStream('stream-2');

      expect(service.hasStream('stream-1')).toBe(true);
      expect(service.hasStream('stream-2')).toBe(true);
      expect(service.getActiveStreamCount()).toBe(2);
    });

    it('should reset stream if started again with same ID', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      service.appendDelta('stream-1', 'Hello');

      service.startStream('stream-1');

      expect(service.getBuffer('stream-1')).toBe('');
    });
  });

  describe('appendDelta', () => {
    it('should append delta to buffer', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      const buffer = service.appendDelta('stream-1', 'Hello');

      expect(buffer).toBe('Hello');
      expect(service.getBuffer('stream-1')).toBe('Hello');
    });

    it('should accumulate multiple deltas', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      service.appendDelta('stream-1', 'Hello');
      service.appendDelta('stream-1', ' ');
      service.appendDelta('stream-1', 'World');

      expect(service.getBuffer('stream-1')).toBe('Hello World');
    });

    it('should throw error if stream does not exist', () => {
      const service = new StreamingMessageService();

      expect(() => service.appendDelta('nonexistent', 'test')).toThrow(
        'Stream not found: nonexistent'
      );
    });

    it('should handle empty deltas', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      service.appendDelta('stream-1', '');

      expect(service.getBuffer('stream-1')).toBe('');
    });

    it('should handle special characters', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      service.appendDelta('stream-1', 'Hello\n');
      service.appendDelta('stream-1', 'World\t!');

      expect(service.getBuffer('stream-1')).toBe('Hello\nWorld\t!');
    });
  });

  describe('setMessageKey', () => {
    it('should set message key for stream', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      service.setMessageKey('stream-1', 'msg-123');

      expect(service.getMessageKey('stream-1')).toBe('msg-123');
    });

    it('should throw error if stream does not exist', () => {
      const service = new StreamingMessageService();

      expect(() => service.setMessageKey('nonexistent', 'msg-123')).toThrow(
        'Stream not found: nonexistent'
      );
    });

    it('should allow updating message key', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      service.setMessageKey('stream-1', 'msg-123');
      service.setMessageKey('stream-1', 'msg-456');

      expect(service.getMessageKey('stream-1')).toBe('msg-456');
    });
  });

  describe('getBuffer', () => {
    it('should return current buffer content', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      service.appendDelta('stream-1', 'Test content');

      expect(service.getBuffer('stream-1')).toBe('Test content');
    });

    it('should throw error if stream does not exist', () => {
      const service = new StreamingMessageService();

      expect(() => service.getBuffer('nonexistent')).toThrow('Stream not found: nonexistent');
    });
  });

  describe('getMessageKey', () => {
    it('should return message key', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      service.setMessageKey('stream-1', 'msg-123');

      expect(service.getMessageKey('stream-1')).toBe('msg-123');
    });

    it('should return null if message key not set', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');

      expect(service.getMessageKey('stream-1')).toBeNull();
    });

    it('should throw error if stream does not exist', () => {
      const service = new StreamingMessageService();

      expect(() => service.getMessageKey('nonexistent')).toThrow('Stream not found: nonexistent');
    });
  });

  describe('hasStream', () => {
    it('should return true for existing stream', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');

      expect(service.hasStream('stream-1')).toBe(true);
    });

    it('should return false for non-existent stream', () => {
      const service = new StreamingMessageService();

      expect(service.hasStream('nonexistent')).toBe(false);
    });

    it('should return false after stream is ended', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      service.endStream('stream-1');

      expect(service.hasStream('stream-1')).toBe(false);
    });
  });

  describe('endStream', () => {
    it('should remove stream from state', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      service.endStream('stream-1');

      expect(service.hasStream('stream-1')).toBe(false);
    });

    it('should not throw error if stream does not exist', () => {
      const service = new StreamingMessageService();

      expect(() => service.endStream('nonexistent')).not.toThrow();
    });

    it('should not affect other streams', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      service.startStream('stream-2');
      service.endStream('stream-1');

      expect(service.hasStream('stream-1')).toBe(false);
      expect(service.hasStream('stream-2')).toBe(true);
    });
  });

  describe('getStreamState', () => {
    it('should return stream state', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      service.appendDelta('stream-1', 'Hello');
      service.setMessageKey('stream-1', 'msg-123');

      const state = service.getStreamState('stream-1');

      expect(state).toEqual({
        buffer: 'Hello',
        messageKey: 'msg-123',
      });
    });

    it('should return undefined for non-existent stream', () => {
      const service = new StreamingMessageService();

      const state = service.getStreamState('nonexistent');

      expect(state).toBeUndefined();
    });
  });

  describe('getActiveStreamCount', () => {
    it('should return 0 initially', () => {
      const service = new StreamingMessageService();

      expect(service.getActiveStreamCount()).toBe(0);
    });

    it('should return count of active streams', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      service.startStream('stream-2');
      service.startStream('stream-3');

      expect(service.getActiveStreamCount()).toBe(3);
    });

    it('should decrease when streams are ended', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      service.startStream('stream-2');
      service.endStream('stream-1');

      expect(service.getActiveStreamCount()).toBe(1);
    });
  });

  describe('clearAllStreams', () => {
    it('should remove all streams', () => {
      const service = new StreamingMessageService();

      service.startStream('stream-1');
      service.startStream('stream-2');
      service.startStream('stream-3');

      service.clearAllStreams();

      expect(service.getActiveStreamCount()).toBe(0);
      expect(service.hasStream('stream-1')).toBe(false);
      expect(service.hasStream('stream-2')).toBe(false);
      expect(service.hasStream('stream-3')).toBe(false);
    });

    it('should handle being called with no streams', () => {
      const service = new StreamingMessageService();

      expect(() => service.clearAllStreams()).not.toThrow();
      expect(service.getActiveStreamCount()).toBe(0);
    });
  });

  describe('complete streaming workflow', () => {
    it('should handle typical streaming narrative workflow', () => {
      const service = new StreamingMessageService();

      // Start stream
      service.startStream('narrative-1');
      expect(service.getBuffer('narrative-1')).toBe('');

      // First chunk arrives
      service.appendDelta('narrative-1', 'The dragon ');
      expect(service.getBuffer('narrative-1')).toBe('The dragon ');

      // Create message in chat, get message key
      service.setMessageKey('narrative-1', 'msg-abc');

      // More chunks arrive
      service.appendDelta('narrative-1', 'awakens ');
      service.appendDelta('narrative-1', 'from its slumber.');

      expect(service.getBuffer('narrative-1')).toBe('The dragon awakens from its slumber.');
      expect(service.getMessageKey('narrative-1')).toBe('msg-abc');

      // Stream completes
      service.endStream('narrative-1');
      expect(service.hasStream('narrative-1')).toBe(false);
    });

    it('should handle concurrent streams', () => {
      const service = new StreamingMessageService();

      // Start two concurrent streams
      service.startStream('narrative-1');
      service.startStream('dialogue-1');

      // Interleaved updates
      service.appendDelta('narrative-1', 'The wizard ');
      service.appendDelta('dialogue-1', 'Hello, ');
      service.setMessageKey('narrative-1', 'msg-1');
      service.appendDelta('narrative-1', 'casts a spell.');
      service.setMessageKey('dialogue-1', 'msg-2');
      service.appendDelta('dialogue-1', 'traveler!');

      // Verify independent states
      expect(service.getBuffer('narrative-1')).toBe('The wizard casts a spell.');
      expect(service.getBuffer('dialogue-1')).toBe('Hello, traveler!');
      expect(service.getMessageKey('narrative-1')).toBe('msg-1');
      expect(service.getMessageKey('dialogue-1')).toBe('msg-2');

      // Clean up
      service.endStream('narrative-1');
      expect(service.hasStream('narrative-1')).toBe(false);
      expect(service.hasStream('dialogue-1')).toBe(true);
    });

    it('should handle error recovery by clearing streams', () => {
      const service = new StreamingMessageService();

      // Start multiple streams
      service.startStream('stream-1');
      service.startStream('stream-2');
      service.appendDelta('stream-1', 'Partial content');

      // Error occurs, clear all streams
      service.clearAllStreams();

      // Verify clean state
      expect(service.getActiveStreamCount()).toBe(0);

      // Can start new streams
      service.startStream('stream-3');
      expect(service.getActiveStreamCount()).toBe(1);
    });
  });
});
