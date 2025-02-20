from flask import Flask, request, jsonify, render_template_string
import os
import logging
from typing import Dict, Any
import asyncio
from functools import wraps
from models.nlp_chain import NLPChain
from models.embedding_service import EmbeddingService
from models.hash_service import HashService
import numpy as np
from hashlib import sha256
import matplotlib.pyplot as plt
import io
import base64
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def async_route(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))
    return wrapped

# Initialize services
try:
    rpc_url = os.environ.get('SOLANA_RPC_URL', 'http://localhost:8899')
    keypair_path = os.environ.get('SOLANA_KEYPAIR_PATH')
    chain = NLPChain(rpc_url=rpc_url, keypair_path=keypair_path)
    # Initialize chain in a separate async context
    asyncio.run(chain.initialize())
    embedding_service = EmbeddingService()
    hash_service = HashService()
    logger.info("Initialized NLP chain with Solana")
except Exception as e:
    logger.error(f"Failed to initialize services: {str(e)}")
    raise

# HTML template for the test interface
TEST_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>NLP Chain Test Interface</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .section { margin-bottom: 30px; padding: 20px; border: 1px solid #ccc; }
        .result { white-space: pre-wrap; background: #f5f5f5; padding: 10px; }
        .highlight { background-color: yellow; }
        button { padding: 10px; margin: 5px; }
        input, textarea { width: 100%; margin: 10px 0; padding: 5px; }
    </style>
</head>
<body>
    <h1>NLP Chain Test Interface</h1>
    
    <div class="section">
        <h2>Add Text Block</h2>
        <textarea id="addText" rows="4" placeholder="Enter text to add"></textarea>
        <input type="number" id="spanLength" value="100" placeholder="Span length">
        <input type="number" id="overlap" value="50" placeholder="Overlap">
        <button onclick="addBlock()">Add Block</button>
        <div id="addResult" class="result"></div>
    </div>

    <div class="section">
        <h2>Search Similar</h2>
        <input type="text" id="searchQuery" placeholder="Enter search query">
        <input type="number" id="threshold" value="0.8" step="0.1" min="0" max="1">
        <button onclick="searchSimilar()">Search</button>
        <div id="searchResult" class="result"></div>
    </div>

    <div class="section">
        <h2>View Block</h2>
        <input type="text" id="blockAddress" placeholder="Enter block address">
        <button onclick="getBlock()">View Block</button>
        <div id="blockResult" class="result"></div>
    </div>

    <div class="section">
        <h2>Analyze Trends</h2>
        <input type="number" id="startBlock" placeholder="Start block (optional)">
        <input type="number" id="endBlock" placeholder="End block (optional)">
        <button onclick="analyzeTrends()">Analyze</button>
        <div id="trendsResult" class="result"></div>
    </div>

    <script>
        async function addBlock() {
            const text = document.getElementById('addText').value;
            const spanLength = parseInt(document.getElementById('spanLength').value);
            const overlap = parseInt(document.getElementById('overlap').value);
            
            const response = await fetch('/blocks', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    text: text,
                    span_length: spanLength,
                    overlap: overlap,
                    metadata: {source: 'test_interface'}
                })
            });
            const result = await response.json();
            document.getElementById('addResult').textContent = JSON.stringify(result, null, 2);
        }

        async function searchSimilar() {
            const query = document.getElementById('searchQuery').value;
            const threshold = document.getElementById('threshold').value;
            
            const response = await fetch(`/search?query=${encodeURIComponent(query)}&threshold=${threshold}`);
            const result = await response.json();
            
            let output = '';
            for (const match of result.matches) {
                const text = match.context;
                const start = match.span.start;
                const end = match.span.end;
                
                output += `Similarity: ${match.similarity}\n`;
                output += `Context: ${text.substring(0, start)}`;
                output += `[${text.substring(start, end)}]`;
                output += `${text.substring(end)}\n\n`;
            }
            
            document.getElementById('searchResult').textContent = output;
        }

        async function getBlock() {
            const blockAddress = document.getElementById('blockAddress').value;
            const response = await fetch(`/blocks/${blockAddress}`);
            const result = await response.json();
            document.getElementById('blockResult').textContent = JSON.stringify(result, null, 2);
        }

        async function analyzeTrends() {
            const startBlock = document.getElementById('startBlock').value;
            const endBlock = document.getElementById('endBlock').value;
            
            let url = '/trends';
            if (startBlock) url += `?start_block=${startBlock}`;
            if (endBlock) url += `${startBlock ? '&' : '?'}end_block=${endBlock}`;
            
            const response = await fetch(url);
            const result = await response.json();
            document.getElementById('trendsResult').textContent = JSON.stringify(result, null, 2);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def test_interface():
    """Render the test interface"""
    return render_template_string(TEST_INTERFACE)

@app.route('/health', methods=['GET'])
@async_route
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    state = await chain.solana.get_chain_state(chain.chain_state)
    return jsonify({
        'status': 'healthy',
        'chain_state': chain.chain_state,
        'block_count': state['block_count']
    })

@app.route('/blocks', methods=['POST'])
@async_route
async def add_block() -> Dict[str, Any]:
    """Add a new block with NLP-processed text"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing text in request body'}), 400
            
        # Get optional parameters
        span_length = int(data.get('span_length', 100))
        overlap = int(data.get('overlap', 50))
        metadata = data.get('metadata', {})
        
        # Add the block
        block_address = await chain.add_block(
            text=data['text'],
            metadata=metadata,
            span_length=span_length,
            overlap=overlap
        )
        
        return jsonify({
            'status': 'success',
            'block_address': block_address
        })
    except Exception as e:
        logger.error(f"Error adding block: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/blocks/<block_address>', methods=['GET'])
@async_route
async def get_block(block_address: str) -> Dict[str, Any]:
    """Get a block by address"""
    try:
        block_data = await chain.get_block(block_address)
        return jsonify(block_data)
    except Exception as e:
        logger.error(f"Error getting block {block_address}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['GET'])
@async_route
async def search_similar() -> Dict[str, Any]:
    """Search for similar text spans"""
    try:
        query = request.args.get('query')
        if not query:
            return jsonify({'error': 'Missing query parameter'}), 400
            
        threshold = float(request.args.get('threshold', 0.8))
        matches = await chain.search_similar(query, threshold)
        
        return jsonify({
            'matches': matches,
            'count': len(matches)
        })
    except Exception as e:
        logger.error(f"Error in similarity search: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/trends', methods=['GET'])
def analyze_trends() -> Dict[str, Any]:
    """Analyze sentiment trends"""
    try:
        start_block = request.args.get('start_block')
        end_block = request.args.get('end_block')
        
        # Convert to integers if provided
        if start_block:
            start_block = int(start_block)
        if end_block:
            end_block = int(end_block)
            
        trends = chain.analyze_trends(
            start_block=start_block if start_block is not None else 0,
            end_block=end_block
        )
        return jsonify(trends)
    except Exception as e:
        logger.error(f"Error analyzing trends: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/test/sample', methods=['POST'])
def add_sample_data() -> Dict[str, Any]:
    """Add sample data for testing"""
    try:
        sample_texts = [
            """Ethereum's latest upgrade has significantly improved transaction speeds and reduced gas fees. 
            The new scaling solution implements advanced sharding techniques, allowing for parallel processing 
            of transactions across multiple chains.""",
            
            """The decentralized finance (DeFi) ecosystem continues to grow with innovative protocols. 
            New lending platforms are implementing advanced risk management systems and improved 
            collateralization mechanisms.""",
            
            """NFT marketplaces are evolving beyond simple art trading platforms. The integration of 
            virtual reality and augmented reality features is creating immersive experiences for digital 
            asset collectors and traders."""
        ]
        
        results = []
        for text in sample_texts:
            block_address = chain.add_block(
                text=text,
                metadata={'source': 'test_data', 'category': 'blockchain'},
                span_length=150,
                overlap=50
            )
            results.append({
                'text': text[:100] + '...',
                'block_address': block_address
            })
        
        return jsonify({
            'status': 'success',
            'blocks_added': len(results),
            'results': results
        })
    except Exception as e:
        logger.error(f"Error adding sample data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/blocks/<int:block_id>/vector', methods=['GET'])
def get_block_vector(block_id: int) -> Dict[str, Any]:
    """Get the vector representation of a block"""
    try:
        block_data = chain.get_block(block_id)
        text = block_data.get('text', '')
        
        # Generate embedding using dedicated service
        vector = embedding_service.generate_embedding(text)
        
        if not any(vector):  # Check if vector is all zeros
            return jsonify({'error': 'Failed to generate meaningful vector'}), 500
            
        return jsonify({
            'block_id': block_id,
            'vector': vector,
            'vector_size': len(vector)
        })
    except Exception as e:
        logger.error(f"Error getting block vector {block_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/blocks/<int:block_id>/hash', methods=['GET'])
def get_block_hash(block_id: int) -> Dict[str, Any]:
    """Get the hash of a block and verify its integrity"""
    try:
        block_data = chain.get_block(block_id)
        text = block_data.get('text', '')
        
        # Create or get block in hash service
        if block_id >= len(hash_service.blocks):
            block = hash_service.create_block(text)
        else:
            block = hash_service.get_block(block_id)
            
        if not block:
            return jsonify({'error': 'Block not found'}), 404
            
        # Verify chain integrity
        chain_status = hash_service.verify_chain()
        
        return jsonify({
            'block_id': block_id,
            'hash': block.hash,
            'previous_hash': block.previous_hash,
            'chain_valid': chain_status['valid'],
            'merkle_root': hash_service.calculate_merkle_root([text])
        })
    except Exception as e:
        logger.error(f"Error generating hash for block {block_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    
    try:
        # Run the Flask app
        app.run(host='0.0.0.0', port=port, debug=True)
    finally:
        # Ensure we close the Solana client
        asyncio.run(chain.close())