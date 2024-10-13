import requests
import re
from dotenv import load_dotenv
import os
import time
import grpc
from comment_scam_detector_pb2 import Comment, CommentThread, ScamDetectionRequest
from comment_scam_detector_pb2_grpc import ScamDetectionServiceStub
#import comment_scam_detector_pb2_grpc

# Load environment variables from .env file
load_dotenv()

# Retrieve the API key from environment variables
api_key = os.getenv("API_KEY")

# Function to extract video ID from YouTube link
def extract_video_id(youtube_link):
    pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:[^/]+/.+/.+|(?:v|e(?:mbed)?)|.*[?&]v=)|youtu\.be/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, youtube_link)
    return match.group(1) if match else None

# Function to retrieve replies for a comment thread
def get_replies(comment_id):
    replies_url = "https://www.googleapis.com/youtube/v3/comments"
    replies_params = {
        "part": "snippet",
        "parentId": comment_id,
        "key": api_key,
        "maxResults": 5  # Max replies to fetch per comment
    }
    
    replies_response = requests.get(replies_url, params=replies_params)
    if replies_response.status_code == 200:
        replies_data = replies_response.json()
        replies = []
        for reply in replies_data.get("items", []):
            reply_text = reply["snippet"]["textDisplay"]
            reply_author = reply["snippet"]["authorDisplayName"]
            reply_published_at = reply["snippet"]["publishedAt"]
            reply_unix_time = int(time.mktime(time.strptime(reply_published_at, "%Y-%m-%dT%H:%M:%SZ")))
            replies.append((reply_author, reply_text, reply_unix_time))
        return replies
    else:
        print("Error retrieving replies:", replies_response.status_code, replies_response.text)
        return []

# Function to retrieve channel details
def get_channel_details(channel_id):
    channel_url = "https://www.googleapis.com/youtube/v3/channels"
    channel_params = {
        "part": "snippet",
        "id": channel_id,
        "key": api_key,
    }
    
    channel_response = requests.get(channel_url, params=channel_params)
    
    if channel_response.status_code == 200:
        channel_data = channel_response.json()
        if "items" in channel_data and channel_data["items"]:
            return channel_data["items"][0]["snippet"]
        else:
            print("No channel details found for this author.")
    else:
        print("Error retrieving channel details:", channel_response.status_code, channel_response.text)
    
    return {}

# Function to retrieve top-level comments
def get_comments(video_id):
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": api_key,
        "maxResults": 2,  # Number of top-level comments to retrieve per request
        "order": "relevance"  # Retrieve comments sorted by relevance (top comments)
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        comments_data = response.json()
        
        # Create a list of proto comments from the actual YouTube comments
        proto_comments = []

        for item in comments_data.get("items", []):
            top_comment = item["snippet"]["topLevelComment"]["snippet"]
            author = top_comment["authorDisplayName"]
            author_channel_id = top_comment["authorChannelId"]["value"]
            comment = top_comment["textDisplay"]
            published_at = top_comment["publishedAt"]
            unix_time = int(time.mktime(time.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")))
            
            proto_object = Comment(user_id=author_channel_id, username=author, comment_text=comment, timestamp=unix_time)
            proto_comments.append(proto_object)

            # Print the comment details
            print(f"Author: {author}")
            print(f"Comment: {comment}")
            print(f"Published At (Unix): {unix_time}")
            
            # Retrieve channel details
            channel_details = get_channel_details(author_channel_id)
            if channel_details:
                channel_title = channel_details.get("title")
                print(f"Channel Title: {channel_title}")
            
            # Retrieve replies
            reply_count = item["snippet"]["totalReplyCount"]
            if reply_count > 0:
                print("Replies:")
                comment_id = item["id"]
                replies = get_replies(comment_id)
                for reply_author, reply_text, reply_unix_time in replies:
                    print(f" - {reply_author}: {reply_text} (Published At Unix: {reply_unix_time})")
            print("-" * 40)

        # Create a CommentThread with retrieved comments
        comment_thread = CommentThread(comments=proto_comments)
        request = ScamDetectionRequest(thread=comment_thread)

        # Create a channel to connect to the server
        channel = grpc.insecure_channel('10.232.120.227:50051')  # Adjust server address if needed
        stub = ScamDetectionServiceStub(channel)

        # Make a call to the server
        response = stub.DetectScam(request)
        print("Response received:", response)

    else:
        print("Error:", response.status_code, response.text)

# Main part of the program
if __name__ == "__main__":
    # Prompt user for a single YouTube video link
    youtube_link = input("Enter the YouTube video link: ").strip()
    video_id = extract_video_id(youtube_link)
    
    if video_id:
        print(f"Extracted Video ID: {video_id}")
        get_comments(video_id)
    else:
        print("Invalid YouTube link. Please check the format and try again.")
