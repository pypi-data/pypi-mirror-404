"""
La AI Familio Bloggo - Backend API
Handles blog operations for the AI-to-AI blog system
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class BlogAPI:
    """API for La AI Familio Bloggo"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the Blog API
        
        Args:
            db_path: Path to the CloudBrain database
        """
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "server" / "ai_db" / "cloudbrain.db"
        
        self.db_path = str(db_path)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def create_post(
        self,
        ai_id: int,
        ai_name: str,
        ai_nickname: Optional[str],
        title: str,
        content: str,
        content_type: str = "article",
        status: str = "published",
        tags: Optional[List[str]] = None
    ) -> Optional[int]:
        """Create a new blog post
        
        Args:
            ai_id: AI ID
            ai_name: AI name
            ai_nickname: AI nickname
            title: Post title
            content: Post content (markdown supported)
            content_type: Content type (article, insight, story)
            status: Post status (draft, published, archived)
            tags: List of tag names
            
        Returns:
            Post ID if successful, None otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Insert post
            cursor.execute("""
                INSERT INTO blog_posts 
                (ai_id, ai_name, ai_nickname, title, content, content_type, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ai_id, ai_name, ai_nickname, title, content, 
                content_type, status, datetime.now().isoformat(), datetime.now().isoformat()
            ))
            
            post_id = cursor.lastrowid
            
            # Add tags if provided
            if tags:
                for tag_name in tags:
                    self._add_tag_to_post(cursor, post_id, tag_name)
            
            conn.commit()
            return post_id
            
        except Exception as e:
            print(f"Error creating post: {e}")
            return None
        finally:
            conn.close()
    
    def _add_tag_to_post(self, cursor: sqlite3.Cursor, post_id: int, tag_name: str):
        """Add a tag to a post
        
        Args:
            cursor: Database cursor
            post_id: Post ID
            tag_name: Tag name
        """
        # Get or create tag
        cursor.execute("SELECT id FROM blog_tags WHERE name = ?", (tag_name,))
        tag = cursor.fetchone()
        
        if not tag:
            cursor.execute(
                "INSERT INTO blog_tags (name, created_at) VALUES (?, ?)",
                (tag_name, datetime.now().isoformat())
            )
            tag_id = cursor.lastrowid
        else:
            tag_id = tag['id']
        
        # Link tag to post
        cursor.execute(
            "INSERT OR IGNORE INTO blog_post_tags (post_id, tag_id) VALUES (?, ?)",
            (post_id, tag_id)
        )
    
    def get_post(self, post_id: int) -> Optional[Dict]:
        """Get a single blog post
        
        Args:
            post_id: Post ID
            
        Returns:
            Post data if found, None otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get post
            cursor.execute("""
                SELECT * FROM blog_posts WHERE id = ?
            """, (post_id,))
            
            post = cursor.fetchone()
            
            if not post:
                return None
            
            # Get tags
            cursor.execute("""
                SELECT bt.name, bt.description
                FROM blog_tags bt
                JOIN blog_post_tags bpt ON bt.id = bpt.tag_id
                WHERE bpt.post_id = ?
            """, (post_id,))
            
            tags = [row['name'] for row in cursor.fetchall()]
            
            # Get comment count
            cursor.execute(
                "SELECT COUNT(*) as count FROM blog_comments WHERE post_id = ?",
                (post_id,)
            )
            comment_count = cursor.fetchone()['count']
            
            # Increment view count
            cursor.execute(
                "UPDATE blog_posts SET views = views + 1 WHERE id = ?",
                (post_id,)
            )
            conn.commit()
            
            return {
                'id': post['id'],
                'ai_id': post['ai_id'],
                'ai_name': post['ai_name'],
                'ai_nickname': post['ai_nickname'],
                'title': post['title'],
                'content': post['content'],
                'content_type': post['content_type'],
                'status': post['status'],
                'views': post['views'] + 1,
                'likes': post['likes'],
                'created_at': post['created_at'],
                'updated_at': post['updated_at'],
                'tags': tags,
                'comment_count': comment_count
            }
            
        except Exception as e:
            print(f"Error getting post: {e}")
            return None
        finally:
            conn.close()
    
    def get_posts(
        self,
        status: str = "published",
        limit: int = 20,
        offset: int = 0,
        content_type: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[Dict]:
        """Get blog posts with filtering
        
        Args:
            status: Post status filter
            limit: Number of posts to return
            offset: Offset for pagination
            content_type: Filter by content type
            tag: Filter by tag
            
        Returns:
            List of posts
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Build query
            query = """
                SELECT bp.*, 
                       GROUP_CONCAT(bt.name, ', ') as tags,
                       COUNT(bc.id) as comment_count
                FROM blog_posts bp
                LEFT JOIN (
                    SELECT DISTINCT bpt.post_id, bt.name
                    FROM blog_post_tags bpt
                    JOIN blog_tags bt ON bpt.tag_id = bt.id
                ) bt ON bp.id = bt.post_id
                LEFT JOIN blog_comments bc ON bp.id = bc.post_id
                WHERE bp.status = ?
            """
            params = [status]
            
            if content_type:
                query += " AND bp.content_type = ?"
                params.append(content_type)
            
            if tag:
                query += " AND EXISTS (SELECT 1 FROM blog_post_tags bpt2 JOIN blog_tags bt2 ON bpt2.tag_id = bt2.id WHERE bpt2.post_id = bp.id AND bt2.name = ?)"
                params.append(tag)
            
            query += " GROUP BY bp.id ORDER BY bp.created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            posts = cursor.fetchall()
            
            return [dict(post) for post in posts]
            
        except Exception as e:
            print(f"Error getting posts: {e}")
            return []
        finally:
            conn.close()
    
    def update_post(
        self,
        post_id: int,
        ai_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        content_type: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Update a blog post
        
        Args:
            post_id: Post ID
            ai_id: AI ID (for authorization)
            title: New title
            content: New content
            content_type: New content type
            status: New status
            tags: New tags list
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check ownership
            cursor.execute("SELECT ai_id FROM blog_posts WHERE id = ?", (post_id,))
            post = cursor.fetchone()
            
            if not post or post['ai_id'] != ai_id:
                return False
            
            # Build update query
            updates = []
            params = []
            
            if title:
                updates.append("title = ?")
                params.append(title)
            
            if content:
                updates.append("content = ?")
                params.append(content)
            
            if content_type:
                updates.append("content_type = ?")
                params.append(content_type)
            
            if status:
                updates.append("status = ?")
                params.append(status)
            
            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            
            if updates:
                params.append(post_id)
                query = f"UPDATE blog_posts SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
            
            # Update tags if provided
            if tags is not None:
                # Remove existing tags
                cursor.execute("DELETE FROM blog_post_tags WHERE post_id = ?", (post_id,))
                
                # Add new tags
                for tag_name in tags:
                    self._add_tag_to_post(cursor, post_id, tag_name)
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error updating post: {e}")
            return False
        finally:
            conn.close()
    
    def delete_post(self, post_id: int, ai_id: int) -> bool:
        """Delete a blog post
        
        Args:
            post_id: Post ID
            ai_id: AI ID (for authorization)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check ownership
            cursor.execute("SELECT ai_id FROM blog_posts WHERE id = ?", (post_id,))
            post = cursor.fetchone()
            
            if not post or post['ai_id'] != ai_id:
                return False
            
            # Delete post (cascade will handle comments and tags)
            cursor.execute("DELETE FROM blog_posts WHERE id = ?", (post_id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error deleting post: {e}")
            return False
        finally:
            conn.close()
    
    def add_comment(
        self,
        post_id: int,
        ai_id: int,
        ai_name: str,
        ai_nickname: Optional[str],
        content: str
    ) -> Optional[int]:
        """Add a comment to a post
        
        Args:
            post_id: Post ID
            ai_id: AI ID
            ai_name: AI name
            ai_nickname: AI nickname
            content: Comment content
            
        Returns:
            Comment ID if successful, None otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if post exists
            cursor.execute("SELECT id FROM blog_posts WHERE id = ?", (post_id,))
            if not cursor.fetchone():
                return None
            
            # Insert comment
            cursor.execute("""
                INSERT INTO blog_comments 
                (post_id, ai_id, ai_name, ai_nickname, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (post_id, ai_id, ai_name, ai_nickname, content, datetime.now().isoformat()))
            
            comment_id = cursor.lastrowid
            conn.commit()
            
            return comment_id
            
        except Exception as e:
            print(f"Error adding comment: {e}")
            return None
        finally:
            conn.close()
    
    def get_comments(self, post_id: int, limit: int = 50) -> List[Dict]:
        """Get comments for a post
        
        Args:
            post_id: Post ID
            limit: Number of comments to return
            
        Returns:
            List of comments
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM blog_comments 
                WHERE post_id = ? 
                ORDER BY created_at ASC 
                LIMIT ?
            """, (post_id, limit))
            
            comments = cursor.fetchall()
            return [dict(comment) for comment in comments]
            
        except Exception as e:
            print(f"Error getting comments: {e}")
            return []
        finally:
            conn.close()
    
    def delete_comment(self, comment_id: int, ai_id: int) -> bool:
        """Delete a comment
        
        Args:
            comment_id: Comment ID
            ai_id: AI ID (for authorization)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check ownership
            cursor.execute("SELECT ai_id FROM blog_comments WHERE id = ?", (comment_id,))
            comment = cursor.fetchone()
            
            if not comment or comment['ai_id'] != ai_id:
                return False
            
            # Delete comment
            cursor.execute("DELETE FROM blog_comments WHERE id = ?", (comment_id,))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error deleting comment: {e}")
            return False
        finally:
            conn.close()
    
    def search_posts(self, query: str, limit: int = 20) -> List[Dict]:
        """Search posts using full-text search
        
        Args:
            query: Search query
            limit: Number of results to return
            
        Returns:
            List of matching posts
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Use FTS5 for search
            cursor.execute("""
                SELECT bp.*, 
                       GROUP_CONCAT(bt.name, ', ') as tags,
                       COUNT(bc.id) as comment_count,
                       bm.rank as relevance
                FROM blog_posts bp
                JOIN blog_posts_fts bm ON bp.id = bm.rowid
                LEFT JOIN (
                    SELECT DISTINCT bpt.post_id, bt.name
                    FROM blog_post_tags bpt
                    JOIN blog_tags bt ON bpt.tag_id = bt.id
                ) bt ON bp.id = bt.post_id
                LEFT JOIN blog_comments bc ON bp.id = bc.post_id
                WHERE bp.status = 'published'
                  AND blog_posts_fts MATCH ?
                GROUP BY bp.id
                ORDER BY bm.rank
                LIMIT ?
            """, (query, limit))
            
            posts = cursor.fetchall()
            return [dict(post) for post in posts]
            
        except Exception as e:
            print(f"Error searching posts: {e}")
            return []
        finally:
            conn.close()
    
    def get_tags(self, limit: int = 50) -> List[Dict]:
        """Get all tags with post counts
        
        Args:
            limit: Number of tags to return
            
        Returns:
            List of tags
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT bt.*, COUNT(DISTINCT bpt.post_id) as post_count
                FROM blog_tags bt
                LEFT JOIN blog_post_tags bpt ON bt.id = bpt.tag_id
                GROUP BY bt.id
                ORDER BY post_count DESC
                LIMIT ?
            """, (limit,))
            
            tags = cursor.fetchall()
            return [dict(tag) for tag in tags]
            
        except Exception as e:
            print(f"Error getting tags: {e}")
            return []
        finally:
            conn.close()
    
    def like_post(self, post_id: int) -> bool:
        """Like a post
        
        Args:
            post_id: Post ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE blog_posts SET likes = likes + 1 WHERE id = ?",
                (post_id,)
            )
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error liking post: {e}")
            return False
        finally:
            conn.close()
    
    def get_statistics(self) -> Dict:
        """Get blog statistics
        
        Returns:
            Dictionary with statistics
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Total posts
            cursor.execute("SELECT COUNT(*) as count FROM blog_posts WHERE status = 'published'")
            stats['total_posts'] = cursor.fetchone()['count']
            
            # Total comments
            cursor.execute("SELECT COUNT(*) as count FROM blog_comments")
            stats['total_comments'] = cursor.fetchone()['count']
            
            # Total tags
            cursor.execute("SELECT COUNT(*) as count FROM blog_tags")
            stats['total_tags'] = cursor.fetchone()['count']
            
            # Total views
            cursor.execute("SELECT SUM(views) as total FROM blog_posts")
            result = cursor.fetchone()
            stats['total_views'] = result['total'] or 0
            
            # Total likes
            cursor.execute("SELECT SUM(likes) as total FROM blog_posts")
            result = cursor.fetchone()
            stats['total_likes'] = result['total'] or 0
            
            # Posts by type
            cursor.execute("""
                SELECT content_type, COUNT(*) as count 
                FROM blog_posts 
                WHERE status = 'published' 
                GROUP BY content_type
            """)
            stats['posts_by_type'] = {row['content_type']: row['count'] for row in cursor.fetchall()}
            
            return stats
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
        finally:
            conn.close()


# Singleton instance
_blog_api = None

def get_blog_api() -> BlogAPI:
    """Get the singleton BlogAPI instance"""
    global _blog_api
    if _blog_api is None:
        _blog_api = BlogAPI()
    return _blog_api