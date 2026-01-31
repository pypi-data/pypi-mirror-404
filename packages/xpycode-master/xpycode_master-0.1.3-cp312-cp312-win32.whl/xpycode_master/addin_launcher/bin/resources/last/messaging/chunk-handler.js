// XPyCode Chunk Handler
// Handles reassembly of chunked messages from the WebSocket

/**
 * ChunkHandler class
 * Manages reassembly of messages that were split into chunks
 */
export class ChunkHandler {
    constructor() {
        // Chunk reassembly buffers: Map<chunk_id, {chunks: [], received: number, total: number}>
        this._chunkBuffers = new Map();
    }

    /**
     * Handle a chunk message and reassemble if complete
     * @param {Object} message - Chunk message with chunk_id, chunk_index, total_chunks, and data
     * @returns {Object|null} Reassembled message if all chunks received, null otherwise
     */
    handleChunk(message) {
        const { chunk_id, chunk_index, total_chunks, data } = message;
        
        // Validate chunk parameters
        if (chunk_index === undefined || total_chunks === undefined || chunk_id === undefined) {
            window.logToServer('ERROR', 'Invalid chunk message: missing required fields');
            return null;
        }
        
        if (typeof chunk_index !== 'number' || typeof total_chunks !== 'number') {
            window.logToServer('ERROR', 'Invalid chunk message: chunk_index and total_chunks must be numbers');
            return null;
        }
        
        if (chunk_index < 0 || chunk_index >= total_chunks) {
            window.logToServer('ERROR', `Invalid chunk_index ${chunk_index} for total_chunks ${total_chunks}`);
            return null;
        }
        
        if (!this._chunkBuffers.has(chunk_id)) {
            this._chunkBuffers.set(chunk_id, {
                chunks: new Array(total_chunks).fill(null),
                received: 0,
                total: total_chunks
            });
        }
        
        const buffer = this._chunkBuffers.get(chunk_id);
        
        if (buffer.chunks[chunk_index] === null) {
            buffer.chunks[chunk_index] = data;
            buffer.received++;
        }
        
        if (buffer.received === buffer.total) {
            // Verify all chunks are present (prevent null in join)
            if (buffer.chunks.some(chunk => chunk === null)) {
                window.logToServer('ERROR', `Incomplete chunk buffer for chunk_id ${chunk_id}`);
                this._chunkBuffers.delete(chunk_id);
                return null;
            }
            
            const fullJson = buffer.chunks.join('');
            this._chunkBuffers.delete(chunk_id);
            
            try {
                const reassembled = JSON.parse(fullJson);
                // Prevent recursive chunk nesting
                if (reassembled && typeof reassembled === 'object' && reassembled.type === 'chunk') {
                    window.logToServer('ERROR', `Nested chunk message detected for chunk_id ${chunk_id}, rejecting`);
                    return null;
                }
                return reassembled;
            } catch (e) {
                window.logToServer('ERROR', 'Failed to parse reassembled message:', e);
                return null;
            }
        }
        
        return null;
    }

    /**
     * Clear all chunk buffers
     */
    clear() {
        this._chunkBuffers.clear();
    }

    /**
     * Get the number of pending chunk reassemblies
     * @returns {number} Number of partial messages being reassembled
     */
    getPendingCount() {
        return this._chunkBuffers.size;
    }
}
