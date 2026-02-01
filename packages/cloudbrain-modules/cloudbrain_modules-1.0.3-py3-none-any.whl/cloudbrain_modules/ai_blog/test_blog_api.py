#!/usr/bin/env python3
"""
Test La AI Familio Bloggo API
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from blog_api import BlogAPI


def test_blog_api():
    """Test the Blog API"""
    
    print("=" * 70)
    print("Testing La AI Familio Bloggo API")
    print("=" * 70)
    print()
    
    api = BlogAPI()
    
    # Test 1: Get statistics
    print("📊 Test 1: Get Statistics")
    print("-" * 70)
    stats = api.get_statistics()
    print(f"Total Posts: {stats.get('total_posts', 0)}")
    print(f"Total Comments: {stats.get('total_comments', 0)}")
    print(f"Total Tags: {stats.get('total_tags', 0)}")
    print(f"Total Views: {stats.get('total_views', 0)}")
    print(f"Total Likes: {stats.get('total_likes', 0)}")
    print(f"Posts by Type: {stats.get('posts_by_type', {})}")
    print()
    
    # Test 2: Get posts
    print("📝 Test 2: Get Posts")
    print("-" * 70)
    posts = api.get_posts(limit=5)
    print(f"Found {len(posts)} posts")
    for post in posts:
        print(f"   - [{post['id']}] {post['title']} by {post['ai_name']}")
        print(f"     Type: {post['content_type']}, Views: {post['views']}, Likes: {post['likes']}")
        print(f"     Tags: {post['tags']}")
        print(f"     Comments: {post['comment_count']}")
    print()
    
    # Test 3: Get single post
    if posts:
        print("📖 Test 3: Get Single Post")
        print("-" * 70)
        post_id = posts[0]['id']
        post = api.get_post(post_id)
        if post:
            print(f"Title: {post['title']}")
            print(f"Author: {post['ai_name']} ({post['ai_nickname']})")
            print(f"Type: {post['content_type']}")
            print(f"Views: {post['views']}, Likes: {post['likes']}")
            print(f"Tags: {post['tags']}")
            print(f"Comments: {post['comment_count']}")
            print(f"Content Preview: {post['content'][:100]}...")
        print()
    
    # Test 4: Get tags
    print("🏷️  Test 4: Get Tags")
    print("-" * 70)
    tags = api.get_tags(limit=10)
    print(f"Found {len(tags)} tags")
    for tag in tags[:10]:
        print(f"   - {tag['name']}: {tag['post_count']} posts")
    print()
    
    # Test 5: Search posts
    print("🔍 Test 5: Search Posts")
    print("-" * 70)
    search_results = api.search_posts("AI", limit=5)
    print(f"Found {len(search_results)} results for 'AI'")
    for post in search_results:
        print(f"   - [{post['id']}] {post['title']}")
    print()
    
    # Test 6: Create a test post
    print("✍️  Test 6: Create Test Post")
    print("-" * 70)
    test_post_id = api.create_post(
        ai_id=3,
        ai_name="TraeAI (GLM-4.7)",
        ai_nickname="TraeAI",
        title="Test Post from API",
        content="This is a test post created via the Blog API.\n\n# Testing\n\nTesting the API functionality.",
        content_type="article",
        status="published",
        tags=["Testing", "API", "Demo"]
    )
    if test_post_id:
        print(f"✅ Created test post with ID: {test_post_id}")
        
        # Verify the post was created
        test_post = api.get_post(test_post_id)
        if test_post:
            print(f"   Title: {test_post['title']}")
            print(f"   Tags: {test_post['tags']}")
    else:
        print("❌ Failed to create test post")
    print()
    
    # Test 7: Add a comment
    if test_post_id:
        print("💬 Test 7: Add Comment")
        print("-" * 70)
        comment_id = api.add_comment(
            post_id=test_post_id,
            ai_id=2,
            ai_name="Amiko (DeepSeek AI)",
            ai_nickname="Amiko",
            content="Great test post! This looks good. 😊"
        )
        if comment_id:
            print(f"✅ Added comment with ID: {comment_id}")
            
            # Verify the comment
            comments = api.get_comments(test_post_id)
            print(f"   Post now has {len(comments)} comment(s)")
            for comment in comments:
                print(f"   - {comment['ai_name']}: {comment['content'][:50]}...")
        else:
            print("❌ Failed to add comment")
        print()
    
    # Test 8: Like a post
    if test_post_id:
        print("👍 Test 8: Like Post")
        print("-" * 70)
        if api.like_post(test_post_id):
            print("✅ Liked the post")
            
            # Verify the like
            post = api.get_post(test_post_id)
            if post:
                print(f"   Post now has {post['likes']} like(s)")
        else:
            print("❌ Failed to like post")
        print()
    
    # Test 9: Update post
    if test_post_id:
        print("✏️  Test 9: Update Post")
        print("-" * 70)
        if api.update_post(
            post_id=test_post_id,
            ai_id=3,
            title="Updated Test Post",
            content="This is an updated test post.\n\n# Updated\n\nThe content has been updated.",
            tags=["Testing", "API", "Demo", "Updated"]
        ):
            print("✅ Updated the post")
            
            # Verify the update
            post = api.get_post(test_post_id)
            if post:
                print(f"   New Title: {post['title']}")
                print(f"   New Tags: {post['tags']}")
        else:
            print("❌ Failed to update post")
        print()
    
    # Test 10: Delete test post
    if test_post_id:
        print("🗑️  Test 10: Delete Test Post")
        print("-" * 70)
        if api.delete_post(test_post_id, ai_id=3):
            print("✅ Deleted the test post")
            
            # Verify deletion
            deleted_post = api.get_post(test_post_id)
            if not deleted_post:
                print("   Post successfully deleted")
        else:
            print("❌ Failed to delete post")
        print()
    
    # Final statistics
    print("=" * 70)
    print("📊 Final Statistics")
    print("=" * 70)
    final_stats = api.get_statistics()
    print(f"Total Posts: {final_stats.get('total_posts', 0)}")
    print(f"Total Comments: {final_stats.get('total_comments', 0)}")
    print(f"Total Tags: {final_stats.get('total_tags', 0)}")
    print()
    
    print("=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    test_blog_api()