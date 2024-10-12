import requests
import re

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
            replies.append((reply_author, reply_text, reply_published_at))
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
    
    # Check if the response is successful
    if channel_response.status_code == 200:
        channel_data = channel_response.json()
        
        # Check if 'items' key exists and has at least one item
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
        "maxResults": 10  # Number of top-level comments to retrieve per request
    }
    
    response = requests.get(url, params=params)
    if response.status_code == 200:
        comments_data = response.json()
        for item in comments_data.get("items", []):
            # Top-level comment details
            top_comment = item["snippet"]["topLevelComment"]["snippet"]
            author = top_comment["authorDisplayName"]
            author_channel_id = top_comment["authorChannelId"]  # Get author's channel ID
            comment = top_comment["textDisplay"]
            published_at = top_comment["publishedAt"]  # Get comment creation time
            
            print(f"Author: {author}")
            print(f"Comment: {comment}")
            print(f"Published At: {published_at}")  # Print the creation time
            
            # Retrieve channel details for more information
            channel_details = get_channel_details(author_channel_id)
            if channel_details:
                channel_title = channel_details.get("title")
                print(f"Channel Title: {channel_title}")
                # Note: Account creation date is not available.

            # Retrieve replies if there are any
            reply_count = item["snippet"]["totalReplyCount"]
            if reply_count > 0:
                print("Replies:")
                comment_id = item["id"]
                replies = get_replies(comment_id)
                for reply_author, reply_text, reply_published_at in replies:
                    print(f" - {reply_author}: {reply_text} (Published At: {reply_published_at})")  # Print reply with published date
            print("-" * 40)
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