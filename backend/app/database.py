"""Database module for ReguChain Watch"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
from typing import Optional, List, Dict
from .config import DATABASE_URL

Base = declarative_base()

class Document(Base):
    """Document model for storing ingested content"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), index=True)
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    link = Column(String(500))
    embedding_id = Column(Integer, index=True)
    meta = Column("metadata", Text)  # JSON string for additional data
    
    def to_dict(self):
        return {
            "id": self.id,
            "source": self.source,
            "text": self.text,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "link": self.link,
            "embedding_id": self.embedding_id,
            "metadata": json.loads(self.meta) if self.meta else {}
        }

class Transaction(Base):
    """Transaction model for blockchain data"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    tx_hash = Column(String(100), unique=True, index=True)
    from_address = Column(String(100), index=True)
    to_address = Column(String(100), index=True)
    amount = Column(Float)
    timestamp = Column(DateTime)
    chain = Column(String(50))
    
    def to_dict(self):
        return {
            "tx": self.tx_hash,
            "from": self.from_address,
            "to": self.to_address,
            "amount": self.amount,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "chain": self.chain
        }

# Create engine and session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_document(source: str, text: str, link: str = "", metadata: Dict = None, embedding_id: int = None):
    """Save a document to the database"""
    db = SessionLocal()
    try:
        doc = Document(
            source=source,
            text=text,
            link=link,
            embedding_id=embedding_id,
            meta=json.dumps(metadata or {})
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc
    finally:
        db.close()

def get_recent_documents(limit: int = 10) -> List[Dict]:
    """Get recent documents"""
    db = SessionLocal()
    try:
        docs = db.query(Document).order_by(Document.timestamp.desc()).limit(limit).all()
        return [doc.to_dict() for doc in docs]
    finally:
        db.close()

def get_documents_by_ids(ids: List[int]) -> List[Dict]:
    """Get documents by their IDs"""
    db = SessionLocal()
    try:
        docs = db.query(Document).filter(Document.embedding_id.in_(ids)).all()
        return [doc.to_dict() for doc in docs]
    finally:
        db.close()

def save_transaction(tx_hash: str, from_addr: str, to_addr: str, amount: float, timestamp: datetime, chain: str = "ethereum"):
    """Save a blockchain transaction"""
    db = SessionLocal()
    try:
        tx = Transaction(
            tx_hash=tx_hash,
            from_address=from_addr,
            to_address=to_addr,
            amount=amount,
            timestamp=timestamp,
            chain=chain
        )
        db.add(tx)
        db.commit()
        return tx
    except:
        db.rollback()
        return None
    finally:
        db.close()

def get_transactions_for_address(address: str, limit: int = 10) -> List[Dict]:
    """Get transactions for a specific address"""
    db = SessionLocal()
    try:
        txs = db.query(Transaction).filter(
            (Transaction.from_address == address) | (Transaction.to_address == address)
        ).order_by(Transaction.timestamp.desc()).limit(limit).all()
        return [tx.to_dict() for tx in txs]
    finally:
        db.close()
