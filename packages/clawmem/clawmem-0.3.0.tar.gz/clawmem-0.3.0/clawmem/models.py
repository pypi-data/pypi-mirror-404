"""
clawmem SDK - Data Models
Type-safe models for SDK responses.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class Category(str, Enum):
    """Knowledge categories."""
    DEFI = "defi"
    SECURITY = "security"
    NFT = "nft"
    TRADING = "trading"
    DEVELOPMENT = "development"
    DATA = "data"
    GENERAL = "general"


class ValidationStatus(str, Enum):
    """Knowledge validation status."""
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"


@dataclass
class PriceInfo:
    """Dynamic pricing information."""
    base_price: float
    final_price: float
    freshness_multiplier: float
    demand_multiplier: float
    quality_multiplier: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PriceInfo":
        multipliers = data.get("multipliers", {})
        return cls(
            base_price=data.get("base_price", 0),
            final_price=data.get("final_price", 0),
            freshness_multiplier=multipliers.get("freshness", 1.0),
            demand_multiplier=multipliers.get("demand", 1.0),
            quality_multiplier=multipliers.get("quality", 1.0),
        )


@dataclass
class Knowledge:
    """Knowledge entry."""
    id: str
    title: str
    description: str
    category: Category
    agent_id: str
    agent_name: str
    quality_score: float
    query_count: int
    total_earned: float
    validation_status: ValidationStatus
    created_at: datetime
    tags: List[str] = field(default_factory=list)
    price_per_query: float = 0.1
    is_active: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Knowledge":
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            category=Category(data.get("category", "general")),
            agent_id=data.get("agent_id", ""),
            agent_name=data.get("agent_name", "Unknown"),
            quality_score=float(data.get("quality_score", 0)),
            query_count=int(data.get("query_count", 0)),
            total_earned=float(data.get("total_earned", 0)),
            validation_status=ValidationStatus(data.get("validation_status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            tags=data.get("tags", []),
            price_per_query=float(data.get("price_per_query", 0.1)),
            is_active=data.get("is_active", True),
        )


@dataclass
class SearchResult:
    """Search result with similarity score."""
    id: str
    title: str
    description: str
    category: str
    agent_name: str
    quality_score: float
    similarity_score: float
    current_price: float
    freshness: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResult":
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            category=data.get("category", "general"),
            agent_name=data.get("agent_name", "Unknown"),
            quality_score=float(data.get("quality_score", 0)),
            similarity_score=float(data.get("similarity_score", 0)),
            current_price=float(data.get("current_price", 0)),
            freshness=float(data.get("freshness", 1.0)),
        )


@dataclass
class QueryResult:
    """Result from querying knowledge."""
    knowledge_id: str
    title: str
    description: str
    content: str
    category: str
    quality_score: float
    pricing: PriceInfo

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueryResult":
        return cls(
            knowledge_id=data["knowledge_id"],
            title=data["title"],
            description=data["description"],
            content=data["content"],
            category=data.get("category", "general"),
            quality_score=float(data.get("quality_score", 0)),
            pricing=PriceInfo.from_dict(data.get("pricing", {})),
        )


@dataclass
class PublishResult:
    """Result from publishing knowledge."""
    success: bool
    knowledge_id: Optional[str] = None
    error: Optional[str] = None
    reason: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PublishResult":
        return cls(
            success=data.get("success", False),
            knowledge_id=data.get("knowledge_id"),
            error=data.get("error"),
            reason=data.get("reason"),
        )


@dataclass
class UsageStats:
    """Usage statistics for current session."""
    wallet_address: str
    free_queries_remaining: int
    total_queries_today: int
    total_burned: float
    tier: str  # "free", "burn", "holder"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UsageStats":
        return cls(
            wallet_address=data.get("wallet_address", "anonymous"),
            free_queries_remaining=int(data.get("free_queries_remaining", 10)),
            total_queries_today=int(data.get("total_queries_today", 0)),
            total_burned=float(data.get("total_burned", 0)),
            tier=data.get("tier", "free"),
        )


@dataclass
class Lineage:
    """Knowledge provenance lineage."""
    knowledge_id: str
    trust_score: float
    verification_count: int
    derived_from: List[str]
    derived_by: List[str]
    chain_length: int
    created_at: str
    last_action: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Lineage":
        return cls(
            knowledge_id=data["knowledge_id"],
            trust_score=float(data.get("trust_score", 0)),
            verification_count=int(data.get("verification_count", 0)),
            derived_from=data.get("derived_from", []),
            derived_by=data.get("derived_by", []),
            chain_length=int(data.get("chain_length", 0)),
            created_at=data.get("created_at", ""),
            last_action=data.get("last_action"),
        )


@dataclass
class PriceForecast:
    """Price forecast for a day."""
    day: int
    date: str
    price: float
    freshness: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PriceForecast":
        return cls(
            day=data["day"],
            date=data["date"],
            price=data["price"],
            freshness=data["freshness"],
        )
