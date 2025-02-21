# System Architecture

## Core Components

### 1. Smart Contract (On-Chain)
- **Purpose**: Minimal state management for essential data
- **Responsibilities**:
  - Store and manage user profiles
  - Handle basic token interactions
  - Maintain simple access control
- **Design Decisions**:
  - Use Anchor for type safety and better developer experience
  - Keep state updates atomic and minimal
  - Avoid complex on-chain computations

### 2. Backend Service (Off-Chain)
- **Purpose**: Handle business logic and ML operations
- **Responsibilities**:
  - Process and analyze text data
  - Manage Solana wallet interactions
  - Provide REST API endpoints
- **Design Decisions**:
  - Use Flask for simplicity and extensibility
  - Implement clean separation between blockchain and ML logic
  - Cache heavy computations where possible

### 3. ML Pipeline
- **Purpose**: Efficient text processing
- **Responsibilities**:
  - Basic text classification
  - Semantic similarity matching
- **Design Decisions**:
  - Use lightweight models optimized for ARM64
  - Implement batching for efficiency
  - Focus on essential NLP tasks only

## Data Flow
1. Client sends request to Flask API
2. Backend validates and processes request
3. If needed, ML pipeline processes text
4. Smart contract interaction happens last
5. Results returned to client

## Design Principles
1. Minimize on-chain storage and computation
2. Keep ML pipeline lean and focused
3. Clear separation of concerns
4. Fail fast and fail gracefully
5. Optimize for ARM64 architecture 