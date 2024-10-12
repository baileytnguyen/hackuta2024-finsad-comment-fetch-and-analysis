import requests
import re
import time
import grpc
from comment_scam_detector_pb2 import Comment, CommentThread, ScamDetectionRequest
from comment_scam_detector_pb2_grpc import ScamDetectionServiceStub
import comment_scam_detector_pb2_grpc
# Replace with your API key
api_key = "AIzaSyBygSCgD-2LuS69wfMvEwz7PgmFOInqgcY"

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
            reply_published_at = reply["snippet"]["publishedAt"]  # Get reply published time
            reply_unix_time = int(time.mktime(time.strptime(reply_published_at, "%Y-%m-%dT%H:%M:%SZ")))  # Convert to Unix time
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
        "maxResults": 5  # Number of top-level comments to retrieve per request
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        comments_data = response.json()
        
        comments = []
        for item in comments_data.get("items", []):
            top_comment = item["snippet"]["topLevelComment"]["snippet"]
            author = top_comment["authorDisplayName"]
            author_channel_id = top_comment["authorChannelId"]  # Get author's channel ID
            comment = top_comment["textDisplay"]
            published_at = top_comment["publishedAt"]  # Get comment creation time
            unix_time = int(time.mktime(time.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")))  # Convert to Unix time
            
            comments.append((author, comment, unix_time, author_channel_id))

        # Sort comments by the desired criteria (for demonstration, sorting by the length of the comment)
        comments.sort(key=lambda x: len(x[1]), reverse=True)  # Change sorting criteria as needed
          
        proto_comments = []
        for author, comment, unix_time, author_channel_id in comments:
            proto_object = Comment("", author, comment, unix_time)
            print(f"Author: {author}")
            print(f"Comment: {comment}")
            print(f"Published At (Unix): {unix_time}")  # Print the creation time in Unix format
            
            # Retrieve channel details for more information
            channel_details = get_channel_details(author_channel_id)
            if channel_details:
                channel_title = channel_details.get("title")
                print(f"Channel Title: {channel_title}")
            
            # Retrieve replies if there are any
            reply_count = item["snippet"]["totalReplyCount"]
            if reply_count > 0:
                print("Replies:")
                comment_id = item["id"]
                replies = get_replies(comment_id)
                for reply_author, reply_text, reply_unix_time in replies:
                    print(f" - {reply_author}: {reply_text} (Published At Unix: {reply_unix_time})")  # Print reply with published date
            print("-" * 40)

            # Create a channel to connect to the server
            channel = grpc.insecure_channel('localhost:50051')  # Adjust to your server address
            stub = comment_scam_detector_pb2_grpc.ScamDetectionServiceStub(channel)  # Replace with your service name

            comment = Comment()
            # Create a request
            request : ScamDetectionRequest = ScamDetectionRequest()  # Replace with your request message type
            # Populate request fields as necessary
            request.field_name = "Your data"  # Set fields according to your proto definition

            # Make a call to the server
            response = stub.DetectScam(request)  # Replace with your method name
            print("Response received:", response)
    else:
        print("Error:", response.status_code, response.text)

# Main part of the program
if __name__ == "__main__":
    youtube_link = input("Enter the YouTube video link: ")
    video_id = extract_video_id(youtube_link)
    
    if video_id:
        print(f"Extracted Video ID: {video_id}")
        # Retrieve and print comments and replies
        get_comments(video_id)
    else:
        print("Invalid YouTube link. Please check the format and try again.")