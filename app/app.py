"""
Minimal Flask Application with Solana Integration
"""
from flask import Flask, request, jsonify
from functools import wraps
import os
from dotenv import load_load_dotenv
from solana.rpc.async_api import AsyncClient
from solana.transaction import Transaction
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .ml.pipeline import MLPipeline
from .blockchain.wallet import SolanaWallet
from .utils.cache import Cache

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize components
ml_pipeline = MLPipeline()
solana_client = AsyncClient(os.getenv("SOLANA_RPC_URL", "http://localhost:8899"))
cache = Cache()

# Thread pool for ML operations
ml_executor = ThreadPoolExecutor(max_workers=2)

def require_wallet(f):
    """Decorator to ensure valid wallet signature."""
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        wallet_address = request.headers.get('X-Wallet-Address')
        signature = request.headers.get('X-Wallet-Signature')
        
        if not wallet_address or not signature:
            return jsonify({'error': 'Missing wallet credentials'}), 401
            
        # Verify wallet signature here
        try:
            # Basic verification for now
            if not SolanaWallet.verify_signature(wallet_address, signature):
                return jsonify({'error': 'Invalid signature'}), 401
        except Exception as e:
            return jsonify({'error': str(e)}), 401
            
        return await f(*args, **kwargs)
    return decorated_function

@app.route('/health')
async def health_check():
    """Basic health check endpoint."""
    try:
        # Check Solana connection
        await solana_client.get_health()
        return jsonify({
            'status': 'healthy',
            'solana': 'connected',
            'ml_pipeline': 'ready'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/process', methods=['POST'])
@require_wallet
async def process_text():
    """Process text with ML pipeline and blockchain integration."""
    try:
        data = request.json
        text = data.get('text')
        
        if not text:
            return jsonify({'error': 'Missing text parameter'}), 400
            
        # Check cache first
        cached_result = cache.get(text)
        if cached_result:
            return jsonify(cached_result)
            
        # Process text in thread pool
        def ml_task():
            result = {
                'embedding': ml_pipeline.get_embedding(text).tolist(),
                'key_info': ml_pipeline.extract_key_info(text)
            }
            if 'categories' in data:
                result['classification'] = ml_pipeline.classify_text(
                    text, data['categories']
                )
            return result
            
        # Run ML processing in thread pool
        result = await asyncio.get_event_loop().run_in_executor(
            ml_executor, ml_task
        )
        
        # Cache result
        cache.set(text, result)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/similarity', methods=['POST'])
@require_wallet
async def compute_similarity():
    """Compute similarity between two texts."""
    try:
        data = request.json
        text1 = data.get('text1')
        text2 = data.get('text2')
        
        if not text1 or not text2:
            return jsonify({'error': 'Missing text parameters'}), 400
            
        # Compute similarity in thread pool
        similarity = await asyncio.get_event_loop().run_in_executor(
            ml_executor,
            lambda: ml_pipeline.compute_similarity(text1, text2)
        )
        
        return jsonify({'similarity': float(similarity)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

# Cleanup
@app.teardown_appcontext
def cleanup(error):
    ml_pipeline.cleanup()
    ml_executor.shutdown(wait=True) 