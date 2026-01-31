import os

# difficulty.py
class DifficultySystem:
    """9-tier difficulty system for mining and transactions"""
    
    def get_bill_difficulty(self, denomination):
        """Get mining difficulty based on bill denomination - 9 tiers"""
        if denomination <= 0:
            return 1  # Handle negative/zero amounts
        elif denomination <= 1:
            return 1  # Trivial
        elif denomination <= 10:
            return 2  # Very Easy
        elif denomination <= 100:
            return 3  # Easy
        elif denomination <= 1000:
            return 4  # Moderate
        elif denomination <= 10000:
            return 5  # Standard
        elif denomination <= 100000:
            return 6  # Challenging
        elif denomination <= 1000000:
            return 7  # Hard
        elif denomination <= 10000000:
            return 8  # Very Hard
        else:
            return 9  # Extreme
    
    def get_transaction_difficulty(self, amount):
        """Get transaction difficulty based on amount - 9 tiers"""
        if amount <= 0:
            return 1  # Handle negative/zero amounts
        elif amount <= 0.001:
            return 1  # Trivial
        elif amount <= 0.01:
            return 2  # Very Easy
        elif amount <= 0.1:
            return 3  # Easy
        elif amount <= 1.0:
            return 4  # Moderate
        elif amount <= 10.0:
            return 5  # Standard
        elif amount <= 100.0:
            return 6  # Challenging
        elif amount <= 1000.0:
            return 7  # Hard
        elif amount <= 10000.0:
            return 8  # Very Hard
        else:
            return 9  # Extreme
    
    def calculate_mining_reward(self, denomination, mining_time):
        """Calculate mining reward with time-based bonus"""
        if denomination <= 0:
            return 0
            
        base_reward = denomination  # Full denomination as base reward
        
        # Time bonus - faster mining gets higher reward
        if mining_time < 10:
            time_bonus = 0.5  # 50% bonus for very fast mining
        elif mining_time < 30:
            time_bonus = 0.2  # 20% bonus for fast mining
        else:
            time_bonus = 0.0  # No bonus for slow mining
            
        return base_reward * (1 + time_bonus)
    
    def calculate_block_reward(
        self,
        difficulty: int,
        block_height: int | None = None,
        tx_count: int = 0,
        fees_total: float = 0.0,
        gtx_denom_total: float = 0.0,
        base_reward: float | None = None,
    ) -> float:
        """Calculate block reward using unified formula.

        Base (exponential): BASE_REWARD * 10^(difficulty - 1)
        Optional components:
        - Fees: FEES * fees_total
        - Transactions: TX_BONUS * min(tx_count, TX_MAX)
        - GTX Genesis: GTX_MULT * gtx_denom_total
        - Halving: apply every LUNALIB_BLOCK_REWARD_HALVING blocks (default 0 = off)
        """
        if difficulty < 1:
            difficulty = 1
        elif difficulty > 9:
            difficulty = 9

        if base_reward is None:
            try:
                base_unit = float(os.getenv("LUNALIB_BLOCK_REWARD_BASE", "0.0001"))
            except Exception:
                base_unit = 0.0001
            base_reward = base_unit * (10 ** (difficulty - 1))

        try:
            base_mult = float(os.getenv("LUNALIB_BLOCK_REWARD_BASE_MULT", "1.0"))
        except Exception:
            base_mult = 1.0

        try:
            fee_mult = float(os.getenv("LUNALIB_BLOCK_REWARD_FEE", "0.0001"))
        except Exception:
            fee_mult = 0.0001

        try:
            tx_bonus = float(os.getenv("LUNALIB_BLOCK_REWARD_TX", "0.00001"))
        except Exception:
            tx_bonus = 0.00001

        try:
            gtx_mult = float(os.getenv("LUNALIB_BLOCK_REWARD_GTX", "0.0001"))
        except Exception:
            gtx_mult = 0.0001

        try:
            tx_bonus_max = int(os.getenv("LUNALIB_BLOCK_REWARD_TX_MAX", "200"))
        except Exception:
            tx_bonus_max = 200

        halving_blocks = 0
        try:
            halving_blocks = int(os.getenv("LUNALIB_BLOCK_REWARD_HALVING", "0"))
        except Exception:
            halving_blocks = 0

        scaled_base = float(base_reward) * base_mult

        if halving_blocks > 0 and block_height is not None and block_height > 0:
            halvings = max(0, int(block_height) // halving_blocks)
            if halvings > 0:
                scaled_base = scaled_base / (2 ** halvings)

        effective_tx_count = int(tx_count or 0)
        if tx_bonus_max > 0:
            effective_tx_count = min(effective_tx_count, tx_bonus_max)

        fees_component = float(fees_total or 0.0) * fee_mult
        tx_component = float(effective_tx_count) * tx_bonus
        gtx_component = float(gtx_denom_total or 0.0) * gtx_mult

        return max(0.0, scaled_base + fees_component + tx_component + gtx_component)

    def gtx_reward_units(self, denomination: float) -> float:
        """Return GTX reward weight as 10^(tier-1) based on denomination tier."""
        try:
            tier = int(self.get_bill_difficulty(float(denomination)))
        except Exception:
            tier = 1
        if tier < 1:
            tier = 1
        if tier > 9:
            tier = 9
        return float(10 ** (tier - 1))
    
    def validate_block_hash(self, block_hash: str, difficulty: int) -> bool:
        """Validate that block hash meets difficulty requirement"""
        if not block_hash or difficulty < 1:
            return False
        
        target_prefix = "0" * difficulty
        return block_hash.startswith(target_prefix)
    
    def validate_block_structure(self, block: dict) -> tuple:
        """Validate block has all required fields
        
        Returns: (is_valid, error_message)
        """
        required_fields = ['index', 'previous_hash', 'timestamp', 'transactions',
                          'miner', 'difficulty', 'nonce', 'hash', 'reward']
        
        for field in required_fields:
            if field not in block:
                return False, f"Missing required field: {field}"
        
        return True, ""
    
    def get_difficulty_name(self, difficulty_level):
        """Get human-readable name for difficulty level"""
        names = {
            1: "Trivial",
            2: "Very Easy", 
            3: "Easy",
            4: "Moderate",
            5: "Standard",
            6: "Challenging",
            7: "Hard",
            8: "Very Hard",
            9: "Extreme"
        }
        return names.get(difficulty_level, "Unknown")
    
    def get_difficulty_color(self, difficulty_level):
        """Get color representation for difficulty level"""
        colors = {
            1: "🟢",  # Green - Trivial
            2: "🟢",  # Green - Very Easy
            3: "🟡",  # Yellow - Easy
            4: "🟡",  # Yellow - Moderate
            5: "🟠",  # Orange - Standard
            6: "🟠",  # Orange - Challenging
            7: "🔴",  # Red - Hard
            8: "🔴",  # Red - Very Hard
            9: "💀"   # Skull - Extreme
        }
        return colors.get(difficulty_level, "⚫")
    
    def get_expected_mining_time(self, difficulty_level, hashrate=1000000):
        """Get expected mining time in seconds based on difficulty and hashrate"""
        if difficulty_level < 1 or difficulty_level > 9:
            return float('inf')
            
        # Rough estimate: each difficulty level increases time by ~16x
        base_time = 0.1  # base time for difficulty 1
        time_multiplier = 16 ** (difficulty_level - 1)
        return base_time * time_multiplier / max(1, hashrate / 1000000)