use anchor_lang::prelude::*;
use anchor_spl::token::{self, Token, TokenAccount};
use sha2::{Sha256, Digest};

declare_id!("Fg6PaFpoGXkYsidMpWTK6W2BeZ7FEfcYkg476zPFsLnS");

#[program]
pub mod minimal {
    use super::*;

    // Initialize a new user profile
    pub fn initialize_user(ctx: Context<InitializeUser>) -> Result<()> {
        let user_profile = &mut ctx.accounts.user_profile;
        user_profile.owner = ctx.accounts.owner.key();
        user_profile.created_at = Clock::get()?.unix_timestamp;
        user_profile.active = true
        Ok(())
    }

    // Update user profile status
    pub fn update_status(ctx: Context<UpdateStatus>, active: bool) -> Result<()> {
        let user_profile = &mut ctx.accounts.user_profile;
        require!(user_profile.owner == ctx.accounts.owner.key(), ErrorCode::Unauthorized);
        
        user_profile.active = active;
        user_profile.updated_at = Clock::get()?.unix_timestamp;
        Ok(())
    }

    // Process token interaction
    pub fn process_interaction(ctx: Context<ProcessInteraction>, amount: u64) -> Result<()> {
        // Transfer tokens
        token::transfer(
            CpiContext::new(
                ctx.accounts.token_program.to_account_info(),
                token::Transfer {
                    from: ctx.accounts.from.to_account_info(),
                    to: ctx.accounts.to.to_account_info(),
                    authority: ctx.accounts.owner.to_account_info(),
                },
            ),
            amount,
        )?;

        Ok(())
    }

    // Submit a proof of hash
    pub fn submit_proof(ctx: Context<SubmitProof>, data_hash: [u8; 32], nonce: u64) -> Result<()> {
        let proof = &mut ctx.accounts.proof;
        let clock = Clock::get()?;

        // Verify the hash meets difficulty requirement
        require!(
            verify_hash_difficulty(&data_hash, 3), // Require 3 leading zeros
            ErrorCode::InvalidProof
        );

        proof.owner = ctx.accounts.owner.key();
        proof.data_hash = data_hash;
        proof.nonce = nonce;
        proof.timestamp = clock.unix_timestamp;
        proof.verified = true;

        Ok(())
    }

    // Verify chain of proofs
    pub fn verify_chain(ctx: Context<VerifyChain>, previous_proof: Pubkey) -> Result<()> {
        let current_proof = &ctx.accounts.current_proof;
        let previous = &ctx.accounts.previous_proof;

        // Verify chronological order
        require!(
            previous.timestamp < current_proof.timestamp,
            ErrorCode::InvalidChain
        );

        // Verify hash chain
        let mut hasher = Sha256::new();
        hasher.update(previous.data_hash);
        hasher.update(current_proof.data_hash);
        let chain_hash = hasher.finalize();

        // Verify chain hash meets difficulty
        require!(
            verify_hash_difficulty(&chain_hash.into(), 2), // Chain requires 2 leading zeros
            ErrorCode::InvalidChain
        );

        Ok(())
    }
}

#[derive(Accounts)]
pub struct InitializeUser<'info> {
    #[account(
        init,
        payer = owner,
        space = UserProfile::LEN,
        seeds = [b"user-profile", owner.key().as_ref()],
        bump
    )]
    pub user_profile: Account<'info, UserProfile>,
    #[account(mut)]
    pub owner: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UpdateStatus<'info> {
    #[account(mut)]
    pub user_profile: Account<'info, UserProfile>,
    pub owner: Signer<'info>,
}

#[derive(Accounts)]
pub struct ProcessInteraction<'info> {
    #[account(mut)]
    pub from: Account<'info, TokenAccount>,
    #[account(mut)]
    pub to: Account<'info, TokenAccount>,
    pub owner: Signer<'info>,
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct SubmitProof<'info> {
    #[account(
        init,
        payer = owner,
        space = ProofData::LEN,
        seeds = [b"proof", owner.key().as_ref(), &Clock::get()?.unix_timestamp.to_le_bytes()],
        bump
    )]
    pub proof: Account<'info, ProofData>,
    #[account(mut)]
    pub owner: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct VerifyChain<'info> {
    #[account(mut)]
    pub current_proof: Account<'info, ProofData>,
    pub previous_proof: Account<'info, ProofData>,
    pub owner: Signer<'info>,
}

#[account]
pub struct UserProfile {
    pub owner: Pubkey,
    pub active: bool,
    pub created_at: i64,
    pub updated_at: i64,
}

impl UserProfile {
    pub const LEN: usize = 8 + // discriminator
        32 + // owner pubkey
        1 +  // active bool
        8 +  // created_at
        8;   // updated_at
}

#[account]
pub struct ProofData {
    pub owner: Pubkey,
    pub data_hash: [u8; 32],
    pub nonce: u64,
    pub timestamp: i64,
    pub verified: bool,
}

impl ProofData {
    pub const LEN: usize = 8 + // discriminator
        32 + // owner pubkey
        32 + // data_hash
        8 +  // nonce
        8 +  // timestamp
        1;   // verified
}

#[error_code]
pub enum ErrorCode {
    #[msg("You are not authorized to perform this action")]
    Unauthorized,
    #[msg("Invalid proof - does not meet difficulty requirement")]
    InvalidProof,
    #[msg("Invalid chain - proofs are not properly linked")]
    InvalidChain,
}

// Helper function to verify hash meets difficulty requirement
fn verify_hash_difficulty(hash: &[u8; 32], leading_zeros: u8) -> bool {
    for i in 0..leading_zeros {
        if hash[i as usize] != 0 {
            return false;
        }
    }
    true
} 