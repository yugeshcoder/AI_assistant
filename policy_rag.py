#!/usr/bin/env python3

"""
FAISS-based RAG system for TechCorp Leave Policy
This module creates embeddings and provides semantic search capabilities
"""

import os
import json
import faiss
import numpy as np
import pickle
from typing import List, Dict, Tuple
import re
import google.generativeai as genai
from config import GOOGLE_API_KEY

class TechCorpPolicyRAG:
    def __init__(self, policy_file: str = "techcorp_leave_policy.txt", index_file: str = "policy_index.faiss"):
        self.policy_file = policy_file
        self.index_file = index_file
        self.chunks_file = "policy_chunks.pkl"
        self.model_name = "models/embedding-001"  # Google's embedding model
        
        # Initialize Google API
        print("Initializing Google Embedding API...")
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # Load or create the FAISS index
        self.chunks = []
        self.index = None
        self.load_or_create_index()
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
        """
        Split text into overlapping chunks for better semantic search
        """
        # Split by sections and paragraphs
        sections = re.split(r'\n\s*\d+\.', text)  # Split by numbered sections
        chunks = []
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
                
            # Clean up section text
            section = section.strip()
            if i > 0:  # Add back the section number (except for the first part)
                section_num = str(i) + ". " + section
            else:
                section_num = section
            
            # Further split long sections into smaller chunks
            words = section_num.split()
            
            if len(words) <= chunk_size:
                # Small section, keep as one chunk
                chunks.append({
                    'text': section_num,
                    'section': i,
                    'words': len(words)
                })
            else:
                # Large section, split into overlapping chunks
                for start in range(0, len(words), chunk_size - overlap):
                    end = min(start + chunk_size, len(words))
                    chunk_text = ' '.join(words[start:end])
                    
                    chunks.append({
                        'text': chunk_text,
                        'section': i,
                        'words': len(words[start:end]),
                        'chunk_start': start,
                        'chunk_end': end
                    })
        
        # Also create smaller focused chunks for specific topics
        focused_chunks = self.create_focused_chunks(text)
        chunks.extend(focused_chunks)
        
        return chunks
    
    def create_focused_chunks(self, text: str) -> List[Dict]:
        """
        Create focused chunks for specific leave types and procedures
        """
        focused_chunks = []
        
        # Define key topics and their patterns
        topics = {
            'casual_leave': [
                r'2\.1 Casual Leave.*?(?=2\.2|3\.)',
                r'Casual Leave.*?(?=Sick Leave|2\.2)',
                r'casual leave.*?(?=\n\n|\n[A-Z])',
            ],
            'sick_leave': [
                r'2\.2 Sick Leave.*?(?=2\.3|3\.)',
                r'Sick Leave.*?(?=Earned Leave|2\.3)',
                r'sick leave.*?(?=\n\n|\n[A-Z])',
            ],
            'earned_leave': [
                r'2\.3 Earned Leave.*?(?=3\.)',
                r'Earned Leave.*?(?=Leave Application|3\.)',
                r'earned leave.*?(?=\n\n|\n[A-Z])',
            ],
            'application_process': [
                r'3\. Leave Application Procedures.*?(?=4\.)',
                r'Application Process.*?(?=Approval Authority)',
                r'application.*?process.*?(?=\n\n|\n[A-Z])',
            ],
            'leave_balance': [
                r'4\. Leave Balance and Tracking.*?(?=5\.)',
                r'Leave Balance.*?(?=Leave Cancellation)',
                r'balance.*?(?=\n\n|\n[A-Z])',
            ]
        }
        
        for topic, patterns in topics.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
                for match in matches:
                    chunk_text = match.group(0).strip()
                    if len(chunk_text) > 50:  # Only include substantial chunks
                        focused_chunks.append({
                            'text': chunk_text,
                            'topic': topic,
                            'words': len(chunk_text.split()),
                            'focused': True
                        })
        
        return focused_chunks
    
    def create_embeddings(self, chunks: List[Dict]) -> np.ndarray:
        """
        Create embeddings for text chunks using Google's embedding API
        """
        texts = [chunk['text'] for chunk in chunks]
        print(f"Creating embeddings for {len(texts)} chunks...")
        
        embeddings = []
        for i, text in enumerate(texts):
            if i % 10 == 0:  # Progress indicator
                print(f"Processing chunk {i+1}/{len(texts)}")
            
            try:
                result = genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
            except Exception as e:
                print(f"Error embedding chunk {i}: {e}")
                # Fallback: create a zero vector
                embeddings.append([0.0] * 768)  # Standard embedding dimension
        
        return np.array(embeddings)
    
    def build_faiss_index(self, embeddings: np.ndarray) -> faiss.Index:
        """
        Build FAISS index for fast similarity search
        """
        print("Building FAISS index...")
        dimension = embeddings.shape[1]
        
        # Use IndexFlatIP for cosine similarity (Inner Product after normalization)
        index = faiss.IndexFlatIP(dimension)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add embeddings to index
        index.add(embeddings.astype('float32'))
        
        print(f"FAISS index built with {index.ntotal} vectors")
        return index
    
    def load_or_create_index(self):
        """
        Load existing index or create a new one
        """
        if os.path.exists(self.index_file) and os.path.exists(self.chunks_file):
            print("Loading existing FAISS index...")
            self.index = faiss.read_index(self.index_file)
            with open(self.chunks_file, 'rb') as f:
                self.chunks = pickle.load(f)
            print(f"Loaded index with {len(self.chunks)} chunks")
        else:
            print("Creating new FAISS index...")
            self.create_index()
    
    def create_index(self):
        """
        Create FAISS index from policy document
        """
        # Read policy document
        if not os.path.exists(self.policy_file):
            raise FileNotFoundError(f"Policy file {self.policy_file} not found")
        
        with open(self.policy_file, 'r', encoding='utf-8') as f:
            policy_text = f.read()
        
        # Create chunks
        print("Creating text chunks...")
        self.chunks = self.chunk_text(policy_text)
        print(f"Created {len(self.chunks)} chunks")
        
        # Create embeddings
        embeddings = self.create_embeddings(self.chunks)
        
        # Build FAISS index
        self.index = self.build_faiss_index(embeddings)
        
        # Save index and chunks
        self.save_index()
    
    def save_index(self):
        """
        Save FAISS index and chunks to disk
        """
        print("Saving FAISS index...")
        faiss.write_index(self.index, self.index_file)
        
        with open(self.chunks_file, 'wb') as f:
            pickle.dump(self.chunks, f)
        
        print("Index saved successfully")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for relevant policy information
        """
        if self.index is None:
            raise ValueError("FAISS index not initialized")
        
        # Create query embedding using Google API
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=query,
                task_type="retrieval_query"
            )
            query_embedding = np.array([result['embedding']])
            faiss.normalize_L2(query_embedding)
        except Exception as e:
            print(f"Error creating query embedding: {e}")
            return []
        
        # Search in FAISS index
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # Return results
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.chunks):  # Valid index
                result = {
                    'text': self.chunks[idx]['text'],
                    'score': float(score),
                    'rank': i + 1,
                    'metadata': {k: v for k, v in self.chunks[idx].items() if k != 'text'}
                }
                results.append(result)
        
        return results
    
    def get_policy_context(self, query: str, max_context_length: int = 2000) -> str:
        """
        Get relevant policy context for a query
        """
        results = self.search(query, top_k=3)
        
        context_parts = []
        total_length = 0
        
        for result in results:
            text = result['text']
            if total_length + len(text) <= max_context_length:
                context_parts.append(f"[Score: {result['score']:.3f}] {text}")
                total_length += len(text)
            else:
                # Truncate if needed
                remaining = max_context_length - total_length
                if remaining > 100:  # Only add if there's meaningful space
                    truncated = text[:remaining-3] + "..."
                    context_parts.append(f"[Score: {result['score']:.3f}] {truncated}")
                break
        
        return "\n\n---\n\n".join(context_parts)
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the RAG system
        """
        if not self.chunks:
            return {"error": "No chunks loaded"}
        
        total_chunks = len(self.chunks)
        focused_chunks = len([c for c in self.chunks if c.get('focused', False)])
        topics = set(c.get('topic', 'general') for c in self.chunks)
        avg_words = sum(c.get('words', 0) for c in self.chunks) / total_chunks
        
        return {
            'total_chunks': total_chunks,
            'focused_chunks': focused_chunks,
            'topics': list(topics),
            'avg_words_per_chunk': round(avg_words, 1),
            'index_size': self.index.ntotal if self.index else 0,
            'model': self.model_name
        }

def test_rag_system():
    """
    Test the RAG system with sample queries
    """
    print("=== Testing TechCorp Policy RAG System ===")
    
    # Initialize RAG system
    rag = TechCorpPolicyRAG()
    
    # Print stats
    stats = rag.get_stats()
    print(f"\nRAG System Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test queries
    test_queries = [
        "How many days of casual leave am I entitled to?",
        "What is the advance notice required for sick leave?",
        "Can I carry forward my earned leave to next year?",
        "What happens if I take leave without approval?",
        "How do I apply for leave in emergency situations?",
        "What is the maximum consecutive days for casual leave?",
        "Medical certificate requirements for sick leave"
    ]
    
    print(f"\n=== Testing {len(test_queries)} queries ===")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        print("-" * 50)
        
        results = rag.search(query, top_k=2)
        for j, result in enumerate(results, 1):
            print(f"Result {j} (Score: {result['score']:.3f}):")
            print(f"  {result['text'][:200]}{'...' if len(result['text']) > 200 else ''}")
        
        # Test context retrieval
        context = rag.get_policy_context(query, max_context_length=500)
        print(f"\nContext length: {len(context)} characters")

if __name__ == "__main__":
    test_rag_system()