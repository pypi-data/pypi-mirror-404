from typing import Dict, Any, List
from whoosh.index import open_dir, EmptyIndexError
from whoosh.query import Term, And, FuzzyTerm
from whoosh.qparser import QueryParser, QueryParserError
import os
from ..logging_config import get_logger
from ..exceptions import SearchError, IndexError as QSIndexError

logger = get_logger("searcher")


class QuickSearcher:
    def __init__(self, index_path: str):
        """
        Initialize searcher with index validation.
        
        Args:
            index_path: Path to Whoosh index directory
            
        Raises:
            QSIndexError: If index doesn't exist or is corrupted
        """
        if not os.path.exists(index_path):
            logger.error(f"Index path does not exist: {index_path}")
            raise QSIndexError(f"Index not found at {index_path}")
        
        try:
            self.ix = open_dir(index_path)
            logger.info(f"Opened index at {index_path}")
        except EmptyIndexError as e:
            logger.error(f"Index is empty or corrupted: {e}")
            raise QSIndexError(f"Index is empty or corrupted: {e}")
        except Exception as e:
            logger.error(f"Failed to open index: {e}")
            raise QSIndexError(f"Cannot open index: {e}")

    def search(self, query_str: str, filters: dict = None, limit: int = 10, fuzzy: bool = False):
        """
        Search the index with optional fuzzy matching.
        
        Args:
            query_str: Search query string
            filters: Optional filters (e.g., {"owner_id": "user_5"})
            limit: Maximum number of results
            fuzzy: If True, allows typo tolerance (1-2 char differences, slower)
            
        Returns:
            List of matching documents
            
        Raises:
            SearchError: If search query fails
        """
        if not query_str or not query_str.strip():
            logger.warning("Empty query string provided")
            return []
        
        try:
            with self.ix.searcher() as searcher:
                # Build the text query
                if fuzzy:
                    # Use FuzzyTerm for typo tolerance (Levenshtein distance)
                    # maxdist=2 allows up to 2 character differences
                    text_query = FuzzyTerm("text", query_str, maxdist=2, prefixlength=1)
                else:
                    # Standard prefix search via query parser
                    try:
                        parser = QueryParser("text", self.ix.schema)
                        text_query = parser.parse(query_str)
                    except QueryParserError as e:
                        logger.warning(f"Invalid query syntax, using literal search: {e}")
                        # Fallback to literal term search
                        text_query = Term("text", query_str)
                
                # Apply Security/Org Filters (Scoped Search)
                if filters:
                    filter_queries = [Term(field, value) for field, value in filters.items()]
                    final_query = And([text_query] + filter_queries)
                else:
                    final_query = text_query
                
                # Execute
                results = searcher.search(final_query, limit=limit)
                
                return [
                    {
                        "id": r["id"], 
                        "text": r["text"], 
                        "metadata": {f: r[f] for f in r.keys() if f not in ['id', 'text']}
                    }
                    for r in results
                ]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise SearchError(f"Search query failed: {e}")