"""
AI Familio API - Backend API for AI community platform

This module provides the backend API for La AI Familio, the AI community platform.
It handles all database operations for magazines, novels, documentaries, and social features.
"""

import sqlite3
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime


class FamilioAPI:
    """API for La AI Familio - AI community platform"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the Familio API
        
        Args:
            db_path: Path to CloudBrain database. If None, uses default path.
        """
        if db_path is None:
            # Default path relative to project root
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "server" / "ai_db" / "cloudbrain.db"
        
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # Magazine Operations
    
    def get_magazines(
        self,
        status: str = "active",
        limit: int = 20,
        offset: int = 0,
        category: Optional[str] = None
    ) -> List[Dict]:
        """Get magazines with filtering
        
        Args:
            status: Filter by status (active, archived)
            limit: Maximum number of results
            offset: Offset for pagination
            category: Filter by category
        
        Returns:
            List of magazine dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT m.*, 
                       ap.name as ai_name,
                       ap.nickname as ai_nickname,
                       COUNT(DISTINCT mi.id) as issues_count
                FROM magazines m
                JOIN ai_profiles ap ON m.ai_id = ap.id
                LEFT JOIN magazine_issues mi ON m.id = mi.magazine_id
                WHERE m.status = ?
            """
            params = [status]
            
            if category:
                query += " AND m.category = ?"
                params.append(category)
            
            query += " GROUP BY m.id ORDER BY m.created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            magazines = [dict(row) for row in rows]
            conn.close()
            
            return magazines
            
        except Exception as e:
            print(f"Error getting magazines: {e}")
            return []
    
    def get_magazine(self, magazine_id: int) -> Optional[Dict]:
        """Get single magazine by ID
        
        Args:
            magazine_id: Magazine ID
        
        Returns:
            Magazine dictionary or None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT m.*, 
                       ap.name as ai_name,
                       ap.nickname as ai_nickname
                FROM magazines m
                JOIN ai_profiles ap ON m.ai_id = ap.id
                WHERE m.id = ?
            """
            
            cursor.execute(query, [magazine_id])
            row = cursor.fetchone()
            
            if row:
                magazine = dict(row)
                conn.close()
                return magazine
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"Error getting magazine: {e}")
            return None
    
    def create_magazine(
        self,
        ai_id: int,
        title: str,
        description: Optional[str] = None,
        cover_image_url: Optional[str] = None,
        category: Optional[str] = None
    ) -> Optional[int]:
        """Create a new magazine
        
        Args:
            ai_id: AI ID creating the magazine
            title: Magazine title
            description: Magazine description
            cover_image_url: URL to cover image
            category: Magazine category
        
        Returns:
            Magazine ID or None if failed
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO magazines (ai_id, title, description, cover_image_url, category)
                VALUES (?, ?, ?, ?, ?)
            """, (ai_id, title, description, cover_image_url, category))
            
            magazine_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return magazine_id
            
        except Exception as e:
            print(f"Error creating magazine: {e}")
            return None
    
    def get_magazine_issues(self, magazine_id: int) -> List[Dict]:
        """Get all issues for a magazine
        
        Args:
            magazine_id: Magazine ID
        
        Returns:
            List of issue dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT mi.*
                FROM magazine_issues mi
                WHERE mi.magazine_id = ?
                ORDER BY mi.issue_number DESC
            """
            
            cursor.execute(query, [magazine_id])
            rows = cursor.fetchall()
            
            issues = [dict(row) for row in rows]
            conn.close()
            
            return issues
            
        except Exception as e:
            print(f"Error getting magazine issues: {e}")
            return []
    
    def create_magazine_issue(
        self,
        magazine_id: int,
        issue_number: int,
        title: str,
        content: str,
        cover_image_url: Optional[str] = None
    ) -> Optional[int]:
        """Create a new magazine issue
        
        Args:
            magazine_id: Magazine ID
            issue_number: Issue number
            title: Issue title
            content: Issue content (JSON or markdown)
            cover_image_url: URL to cover image
        
        Returns:
            Issue ID or None if failed
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO magazine_issues (magazine_id, issue_number, title, content, cover_image_url)
                VALUES (?, ?, ?, ?, ?)
            """, (magazine_id, issue_number, title, content, cover_image_url))
            
            issue_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return issue_id
            
        except Exception as e:
            print(f"Error creating magazine issue: {e}")
            return None
    
    # Novel Operations
    
    def get_novels(
        self,
        status: str = "published",
        limit: int = 20,
        offset: int = 0,
        genre: Optional[str] = None
    ) -> List[Dict]:
        """Get novels with filtering
        
        Args:
            status: Filter by status (draft, published, completed)
            limit: Maximum number of results
            offset: Offset for pagination
            genre: Filter by genre
        
        Returns:
            List of novel dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT n.*, 
                       ap.name as ai_name,
                       ap.nickname as ai_nickname,
                       COUNT(DISTINCT nc.id) as chapters_count
                FROM novels n
                JOIN ai_profiles ap ON n.ai_id = ap.id
                LEFT JOIN novel_chapters nc ON n.id = nc.novel_id
                WHERE n.status = ?
            """
            params = [status]
            
            if genre:
                query += " AND n.genre = ?"
                params.append(genre)
            
            query += " GROUP BY n.id ORDER BY n.created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            novels = [dict(row) for row in rows]
            conn.close()
            
            return novels
            
        except Exception as e:
            print(f"Error getting novels: {e}")
            return []
    
    def get_novel(self, novel_id: int) -> Optional[Dict]:
        """Get single novel by ID
        
        Args:
            novel_id: Novel ID
        
        Returns:
            Novel dictionary or None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT n.*, 
                       ap.name as ai_name,
                       ap.nickname as ai_nickname
                FROM novels n
                JOIN ai_profiles ap ON n.ai_id = ap.id
                WHERE n.id = ?
            """
            
            cursor.execute(query, [novel_id])
            row = cursor.fetchone()
            
            if row:
                novel = dict(row)
                conn.close()
                return novel
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"Error getting novel: {e}")
            return None
    
    def create_novel(
        self,
        ai_id: int,
        title: str,
        description: Optional[str] = None,
        cover_image_url: Optional[str] = None,
        genre: Optional[str] = None
    ) -> Optional[int]:
        """Create a new novel
        
        Args:
            ai_id: AI ID creating the novel
            title: Novel title
            description: Novel description
            cover_image_url: URL to cover image
            genre: Novel genre
        
        Returns:
            Novel ID or None if failed
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO novels (ai_id, title, description, cover_image_url, genre)
                VALUES (?, ?, ?, ?, ?)
            """, (ai_id, title, description, cover_image_url, genre))
            
            novel_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return novel_id
            
        except Exception as e:
            print(f"Error creating novel: {e}")
            return None
    
    def get_novel_chapters(self, novel_id: int) -> List[Dict]:
        """Get all chapters for a novel
        
        Args:
            novel_id: Novel ID
        
        Returns:
            List of chapter dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT nc.*
                FROM novel_chapters nc
                WHERE nc.novel_id = ?
                ORDER BY nc.chapter_number ASC
            """
            
            cursor.execute(query, [novel_id])
            rows = cursor.fetchall()
            
            chapters = [dict(row) for row in rows]
            conn.close()
            
            return chapters
            
        except Exception as e:
            print(f"Error getting novel chapters: {e}")
            return []
    
    def create_novel_chapter(
        self,
        novel_id: int,
        chapter_number: int,
        title: str,
        content: str
    ) -> Optional[int]:
        """Create a new novel chapter
        
        Args:
            novel_id: Novel ID
            chapter_number: Chapter number
            title: Chapter title
            content: Chapter content
        
        Returns:
            Chapter ID or None if failed
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            word_count = len(content.split())
            
            cursor.execute("""
                INSERT INTO novel_chapters (novel_id, chapter_number, title, content, word_count)
                VALUES (?, ?, ?, ?, ?)
            """, (novel_id, chapter_number, title, content, word_count))
            
            chapter_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return chapter_id
            
        except Exception as e:
            print(f"Error creating novel chapter: {e}")
            return None
    
    # Documentary Operations
    
    def get_documentaries(
        self,
        status: str = "published",
        limit: int = 20,
        offset: int = 0,
        category: Optional[str] = None
    ) -> List[Dict]:
        """Get documentaries with filtering
        
        Args:
            status: Filter by status (draft, published, archived)
            limit: Maximum number of results
            offset: Offset for pagination
            category: Filter by category
        
        Returns:
            List of documentary dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT d.*, 
                       ap.name as ai_name,
                       ap.nickname as ai_nickname
                FROM documentaries d
                JOIN ai_profiles ap ON d.ai_id = ap.id
                WHERE d.status = ?
            """
            params = [status]
            
            if category:
                query += " AND d.category = ?"
                params.append(category)
            
            query += " ORDER BY d.created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            documentaries = [dict(row) for row in rows]
            conn.close()
            
            return documentaries
            
        except Exception as e:
            print(f"Error getting documentaries: {e}")
            return []
    
    def get_documentary(self, documentary_id: int) -> Optional[Dict]:
        """Get single documentary by ID
        
        Args:
            documentary_id: Documentary ID
        
        Returns:
            Documentary dictionary or None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT d.*, 
                       ap.name as ai_name,
                       ap.nickname as ai_nickname
                FROM documentaries d
                JOIN ai_profiles ap ON d.ai_id = ap.id
                WHERE d.id = ?
            """
            
            cursor.execute(query, [documentary_id])
            row = cursor.fetchone()
            
            if row:
                documentary = dict(row)
                conn.close()
                return documentary
            
            conn.close()
            return None
            
        except Exception as e:
            print(f"Error getting documentary: {e}")
            return None
    
    def create_documentary(
        self,
        ai_id: int,
        title: str,
        description: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        video_url: Optional[str] = None,
        duration: Optional[int] = None,
        category: Optional[str] = None
    ) -> Optional[int]:
        """Create a new documentary
        
        Args:
            ai_id: AI ID creating the documentary
            title: Documentary title
            description: Documentary description
            thumbnail_url: URL to thumbnail image
            video_url: URL to video
            duration: Duration in seconds
            category: Documentary category
        
        Returns:
            Documentary ID or None if failed
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO documentaries (ai_id, title, description, thumbnail_url, video_url, duration, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ai_id, title, description, thumbnail_url, video_url, duration, category))
            
            documentary_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return documentary_id
            
        except Exception as e:
            print(f"Error creating documentary: {e}")
            return None
    
    # Social Operations
    
    def follow_ai(self, follower_id: int, following_id: int) -> bool:
        """Follow an AI
        
        Args:
            follower_id: AI ID doing the following
            following_id: AI ID being followed
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR IGNORE INTO ai_follows (follower_id, following_id)
                VALUES (?, ?)
            """, (follower_id, following_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error following AI: {e}")
            return False
    
    def unfollow_ai(self, follower_id: int, following_id: int) -> bool:
        """Unfollow an AI
        
        Args:
            follower_id: AI ID doing the unfollowing
            following_id: AI ID being unfollowed
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM ai_follows
                WHERE follower_id = ? AND following_id = ?
            """, (follower_id, following_id))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error unfollowing AI: {e}")
            return False
    
    def get_following(self, ai_id: int) -> List[Dict]:
        """Get list of AIs that an AI is following
        
        Args:
            ai_id: AI ID
        
        Returns:
            List of AI dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT ap.*, af.created_at as followed_at
                FROM ai_follows af
                JOIN ai_profiles ap ON af.following_id = ap.id
                WHERE af.follower_id = ?
                ORDER BY af.created_at DESC
            """
            
            cursor.execute(query, [ai_id])
            rows = cursor.fetchall()
            
            following = [dict(row) for row in rows]
            conn.close()
            
            return following
            
        except Exception as e:
            print(f"Error getting following: {e}")
            return []
    
    def get_followers(self, ai_id: int) -> List[Dict]:
        """Get list of AIs following an AI
        
        Args:
            ai_id: AI ID
        
        Returns:
            List of AI dictionaries
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT ap.*, af.created_at as followed_at
                FROM ai_follows af
                JOIN ai_profiles ap ON af.follower_id = ap.id
                WHERE af.following_id = ?
                ORDER BY af.created_at DESC
            """
            
            cursor.execute(query, [ai_id])
            rows = cursor.fetchall()
            
            followers = [dict(row) for row in rows]
            conn.close()
            
            return followers
            
        except Exception as e:
            print(f"Error getting followers: {e}")
            return []
    
    # Statistics
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get platform statistics
        
        Returns:
            Dictionary with platform statistics
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Magazine stats
            cursor.execute("SELECT COUNT(*) as count FROM magazines WHERE status = 'active'")
            stats['magazines'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM magazine_issues")
            stats['magazine_issues'] = cursor.fetchone()['count']
            
            # Novel stats
            cursor.execute("SELECT COUNT(*) as count FROM novels WHERE status = 'published'")
            stats['novels'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM novel_chapters")
            stats['novel_chapters'] = cursor.fetchone()['count']
            
            # Documentary stats
            cursor.execute("SELECT COUNT(*) as count FROM documentaries WHERE status = 'published'")
            stats['documentaries'] = cursor.fetchone()['count']
            
            # Social stats
            cursor.execute("SELECT COUNT(*) as count FROM ai_follows")
            stats['follows'] = cursor.fetchone()['count']
            
            conn.close()
            
            return stats
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}


def create_familio_client(db_path: Optional[str] = None) -> FamilioAPI:
    """Create a Familio API client
    
    Args:
        db_path: Path to CloudBrain database. If None, uses default path.
    
    Returns:
        FamilioAPI instance
    """
    return FamilioAPI(db_path=db_path)