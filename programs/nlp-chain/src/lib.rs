use anchor_lang::prelude::*;
use anchor_lang::solana_program::hash::{hash, Hash};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod nlp_chain {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        let chain_state = &mut ctx.accounts.chain_state;
        chain_state.authority = ctx.accounts.authority.key();
        chain_state.block_count = 0;
        chain_state.last_hash = hash(&[0; 32]);
        Ok(())
    }

    pub fn add_block(
        ctx: Context<AddBlock>,
        text: String,
        vector: Vec<f64>,
        metadata: String,
    ) -> Result<()> {
        let chain_state = &mut ctx.accounts.chain_state;
        let block = &mut ctx.accounts.block;

        // Update block data
        block.authority = ctx.accounts.authority.key();
        block.index = chain_state.block_count;
        block.timestamp = Clock::get()?.unix_timestamp;
        block.text = text;
        block.vector = vector;
        block.metadata = metadata;
        
        // Calculate and store hashes
        let data_hash = hash(&block.text.as_bytes());
        block.data_hash = data_hash;
        block.previous_hash = chain_state.last_hash;
        
        // Update chain state
        chain_state.last_hash = data_hash;
        chain_state.block_count += 1;

        Ok(())
    }

    pub fn update_vector(
        ctx: Context<UpdateVector>,
        new_vector: Vec<f64>
    ) -> Result<()> {
        let block = &mut ctx.accounts.block;
        require!(
            ctx.accounts.authority.key() == block.authority,
            NLPChainError::UnauthorizedUpdate
        );
        
        block.vector = new_vector;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = authority,
        space = ChainState::LEN
    )]
    pub chain_state: Account<'info, ChainState>,
    
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct AddBlock<'info> {
    #[account(
        init,
        payer = authority,
        space = Block::LEN,
        seeds = [b"block", chain_state.block_count.to_le_bytes().as_ref()],
        bump
    )]
    pub block: Account<'info, Block>,
    
    #[account(mut)]
    pub chain_state: Account<'info, ChainState>,
    
    #[account(mut)]
    pub authority: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateVector<'info> {
    #[account(mut)]
    pub block: Account<'info, Block>,
    pub authority: Signer<'info>,
}

#[account]
pub struct ChainState {
    pub authority: Pubkey,
    pub block_count: u64,
    pub last_hash: Hash,
}

impl ChainState {
    pub const LEN: usize = 8 + // discriminator
        32 + // authority
        8 + // block_count
        32; // last_hash
}

#[account]
pub struct Block {
    pub authority: Pubkey,
    pub index: u64,
    pub timestamp: i64,
    pub text: String,
    pub vector: Vec<f64>,
    pub metadata: String,
    pub data_hash: Hash,
    pub previous_hash: Hash,
}

impl Block {
    pub const LEN: usize = 8 + // discriminator
        32 + // authority
        8 + // index
        8 + // timestamp
        4 + 1000 + // text (max 1000 chars)
        4 + 768 * 8 + // vector (max 768 f64 values)
        4 + 500 + // metadata (max 500 chars)
        32 + // data_hash
        32; // previous_hash
}

#[error_code]
pub enum NLPChainError {
    #[msg("Only the authority can update block data")]
    UnauthorizedUpdate,
} 