import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.core.schemas import RawComment, VideoMetadata

# Load environment variables
load_dotenv()

def get_youtube_client():
    """Initializes and returns the YouTube Data API client."""
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY environment variable is missing.")
    return build("youtube", "v3", developerKey=api_key)

def run_video_metadata(video_id: str) -> VideoMetadata:
    """Fetches video metadata (title, channel, views, thumbnail)."""
    youtube = get_youtube_client()
    try:
        response = youtube.videos().list(
            part="snippet,statistics",
            id=video_id
        ).execute()
        
        if not response.get("items"):
            raise ValueError(f"Video {video_id} not found.")
            
        item = response["items"][0]
        snippet = item["snippet"]
        statistics = item["statistics"]
        
        # Get highest res thumbnail available
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = thumbnails.get("maxres", thumbnails.get("high", thumbnails.get("default", {}))).get("url", "")
        return VideoMetadata(
            title=snippet.get("title", "Unknown Title"),
            channel_title=snippet.get("channelTitle", "Unknown Channel"),
            view_count=int(statistics.get("viewCount", 0)),
            thumbnail_url=thumbnail_url
        )
    except HttpError as e:
        print(f"An HTTP error occurred fetching metadata: {e}")
        raise

def run_ingestion(video_id: str, max_comments: int = 2000) -> list[RawComment]:
    """
    Fetches comments from a YouTube video up to max_comments.
    Handles pagination and nested replies.
    Acts as a circuit breaker if comments are disabled.
    """
    youtube = get_youtube_client()
    comments_list: list[RawComment] = []
    
    try:
        # Initial request
        request = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=100,  # Max allowed by API per page
            textFormat="plainText"
        )
        
        while request and len(comments_list) < max_comments:
            response = request.execute()
            
            for item in response.get("items", []):
                if len(comments_list) >= max_comments:
                    break
                    
                # Extract top-level comment
                top_level_comment = item["snippet"]["topLevelComment"]["snippet"]
                
                # Parse datetime string to datetime object
                published_at_str = top_level_comment.get("publishedAt")
                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00")) if published_at_str else datetime.now(timezone.utc)
                
                raw_comment = RawComment(
                    comment_id=item["snippet"]["topLevelComment"]["id"],
                    author=top_level_comment.get("authorDisplayName", "Unknown"),
                    text_display=top_level_comment.get("textDisplay", ""),
                    like_count=top_level_comment.get("likeCount", 0),
                    published_at=published_at
                )
                comments_list.append(raw_comment)
                
                # Extract replies if any, and if we still have room
                if "replies" in item and len(comments_list) < max_comments:
                    for reply_item in item["replies"].get("comments", []):
                        if len(comments_list) >= max_comments:
                            break
                            
                        reply_snippet = reply_item["snippet"]
                        reply_published_at_str = reply_snippet.get("publishedAt")
                        reply_published_at = datetime.fromisoformat(reply_published_at_str.replace("Z", "+00:00")) if reply_published_at_str else datetime.now(timezone.utc)

                        reply_comment = RawComment(
                            comment_id=reply_item["id"],
                            author=reply_snippet.get("authorDisplayName", "Unknown"),
                            text_display=reply_snippet.get("textDisplay", ""),
                            like_count=reply_snippet.get("likeCount", 0),
                            published_at=reply_published_at
                        )
                        comments_list.append(reply_comment)

            # Get the next page token
            if "nextPageToken" in response:
                request = youtube.commentThreads().list(
                    part="snippet,replies",
                    videoId=video_id,
                    maxResults=100,
                    textFormat="plainText",
                    pageToken=response["nextPageToken"]
                )
            else:
                break
                
    except HttpError as e:
        if e.resp.status == 403 and "disabled comments" in str(e).lower():
            print(f"Comments are disabled for video {video_id}.")
            return []
        else:
            print(f"An HTTP error occurred: {e}")
            raise
            
    return comments_list
