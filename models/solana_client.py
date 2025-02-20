from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from solana.keypair import Keypair
from solana.system_program import SYS_PROGRAM_ID
from solana.transaction import Transaction
from solana.rpc.types import TxOpts
from anchorpy import Program, Provider, Wallet
import json
import base64
from typing import List, Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)

class SolanaNLPChain:
    """Client for interacting with the Solana NLP Chain program"""
    
    PROGRAM_ID = "Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS"
    
    def __init__(self, 
                 rpc_url: str = "http://localhost:8899",
                 keypair_path: Optional[str] = None):
        """
        Initialize Solana client
        
        Args:
            rpc_url: Solana RPC URL
            keypair_path: Path to keypair file (creates new if None)
        """
        self.rpc_url = rpc_url
        
        # Load or create keypair
        if keypair_path and os.path.exists(keypair_path):
            with open(keypair_path, 'r') as f:
                keypair_bytes = bytes(json.load(f))
                self.keypair = Keypair.from_secret_key(keypair_bytes)
        else:
            self.keypair = Keypair()
            if keypair_path:
                os.makedirs(os.path.dirname(keypair_path), exist_ok=True)
                with open(keypair_path, 'w') as f:
                    json.dump(list(self.keypair.secret_key), f)
        
        # Initialize Solana client
        self.client = AsyncClient(rpc_url, commitment=Commitment.CONFIRMED)
        self.provider = Provider(
            self.client,
            Wallet(self.keypair),
            opts=TxOpts(skip_preflight=True)
        )
        
        # Load program
        with open('target/idl/nlp_chain.json', 'r') as f:
            idl = json.load(f)
        self.program = Program(idl, self.PROGRAM_ID, self.provider)
        
        logger.info(f"Initialized Solana client with program ID: {self.PROGRAM_ID}")

    async def initialize(self) -> str:
        """Initialize the NLP chain program"""
        try:
            # Create chain state account
            chain_state = Keypair()
            
            # Build and send transaction
            tx = await self.program.rpc["initialize"](
                ctx=self.program.context(
                    accounts={
                        "chain_state": chain_state.public_key,
                        "authority": self.keypair.public_key,
                        "system_program": SYS_PROGRAM_ID,
                    }
                )
            )
            
            logger.info(f"Initialized chain state: {chain_state.public_key}")
            return str(chain_state.public_key)
            
        except Exception as e:
            logger.error(f"Failed to initialize chain: {str(e)}")
            raise

    async def add_block(self,
                       text: str,
                       vector: List[float],
                       metadata: Dict[str, Any],
                       chain_state: str) -> str:
        """
        Add a new block to the chain
        
        Args:
            text: Text content
            vector: Vector embedding
            metadata: Additional metadata
            chain_state: Chain state account address
            
        Returns:
            Block account address
        """
        try:
            # Create block account
            block = Keypair()
            
            # Convert metadata to string
            metadata_str = json.dumps(metadata)
            
            # Build and send transaction
            tx = await self.program.rpc["add_block"](
                text,
                vector,
                metadata_str,
                ctx=self.program.context(
                    accounts={
                        "block": block.public_key,
                        "chain_state": chain_state,
                        "authority": self.keypair.public_key,
                        "system_program": SYS_PROGRAM_ID,
                    }
                )
            )
            
            logger.info(f"Added block: {block.public_key}")
            return str(block.public_key)
            
        except Exception as e:
            logger.error(f"Failed to add block: {str(e)}")
            raise

    async def update_vector(self,
                          block_address: str,
                          new_vector: List[float]) -> None:
        """
        Update vector embedding for a block
        
        Args:
            block_address: Block account address
            new_vector: New vector embedding
        """
        try:
            # Build and send transaction
            tx = await self.program.rpc["update_vector"](
                new_vector,
                ctx=self.program.context(
                    accounts={
                        "block": block_address,
                        "authority": self.keypair.public_key,
                    }
                )
            )
            
            logger.info(f"Updated vector for block: {block_address}")
            
        except Exception as e:
            logger.error(f"Failed to update vector: {str(e)}")
            raise

    async def get_block(self, block_address: str) -> Dict[str, Any]:
        """
        Get block data
        
        Args:
            block_address: Block account address
            
        Returns:
            Block data
        """
        try:
            block = await self.program.account["Block"].fetch(block_address)
            
            return {
                "authority": str(block.authority),
                "index": block.index,
                "timestamp": block.timestamp,
                "text": block.text,
                "vector": block.vector,
                "metadata": json.loads(block.metadata),
                "data_hash": base64.b64encode(block.data_hash).decode('utf-8'),
                "previous_hash": base64.b64encode(block.previous_hash).decode('utf-8')
            }
            
        except Exception as e:
            logger.error(f"Failed to get block {block_address}: {str(e)}")
            raise

    async def get_chain_state(self, chain_state: str) -> Dict[str, Any]:
        """
        Get chain state
        
        Args:
            chain_state: Chain state account address
            
        Returns:
            Chain state data
        """
        try:
            state = await self.program.account["ChainState"].fetch(chain_state)
            
            return {
                "authority": str(state.authority),
                "block_count": state.block_count,
                "last_hash": base64.b64encode(state.last_hash).decode('utf-8')
            }
            
        except Exception as e:
            logger.error(f"Failed to get chain state: {str(e)}")
            raise

    async def close(self):
        """Close the Solana client connection"""
        await self.client.close() 