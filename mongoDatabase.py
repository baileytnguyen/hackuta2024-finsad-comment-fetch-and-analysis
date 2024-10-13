import requests
import re
import time
from dotenv import load_dotenv
import os
from pymongo import MongoClient

# Load environment variables from .env file
load_dotenv()

# Retrieve the API key from environment variables
api_key = os.getenv("API_KEY")

# MongoDB connection URI
mongo_uri = "mongodb://localhost:27017"

# Connect to MongoDB
client = MongoClient(mongo_uri)
db = client.youtube_comments_database  # Use or create a database
comments_collection = db.comments  # Use or create a collection

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
            replies.append({
                'author': reply_author,
                'author_channel_id': reply["snippet"]["authorChannelId"]["value"],
                'comment_text': reply_text,
                'timestamp': reply_unix_time,
                'published_at': reply_published_at,
            })
        return replies
    else:
        print("Error retrieving replies:", replies_response.status_code, replies_response.text)
        return []

# Function to retrieve comments and store them in MongoDB
def get_comments_and_store(video_id):
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "key": api_key,
        "maxResults": 10,
        "order": "relevance"
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        comments_data = response.json().get("items", [])
        for item in comments_data:
            top_comment_snippet = item["snippet"]["topLevelComment"]["snippet"]
            author = top_comment_snippet["authorDisplayName"]
            author_channel_id = top_comment_snippet["authorChannelId"]["value"]
            comment = top_comment_snippet["textDisplay"]
            published_at = top_comment_snippet["publishedAt"]
            unix_time = int(time.mktime(time.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")))

            # Prepare the comment document with replies
            comment_doc = {
                'top_comment': {
                    'author': author,
                    'author_channel_id': author_channel_id,
                    'comment_text': comment,
                    'timestamp': unix_time,
                    'published_at': published_at,
                },
                'replies': []  # Initialize replies as an empty list
            }

            # Insert the top comment document into MongoDB
            comment_id = comments_collection.insert_one(comment_doc).inserted_id
            print(f"Inserted top comment by {author} into MongoDB.")

            # Retrieve replies for the top comment
            reply_count = item["snippet"]["totalReplyCount"]
            if reply_count > 0:
                replies = get_replies(item["id"])
                for reply in replies:
                    # Append each reply to the replies array of the top comment
                    comments_collection.update_one(
                        {'_id': comment_id},
                        {'$push': {'replies': reply}}
                    )
                    print(f"Inserted reply by {reply['author']} into MongoDB.")

    else:
        print("Error fetching comments:", response.status_code, response.text)

# Function to handle inputted YouTube links and store comments in MongoDB
def save_comments_from_links(youtube_links):
    for link in youtube_links:
        video_id = extract_video_id(link)
        if video_id:
            get_comments_and_store(video_id)
        else:
            print(f"Invalid YouTube link: {link}")

# Main section: get user input for YouTube links
youtube_links_input = input("Enter YouTube links separated by commas: ")
youtube_links = [link.strip() for link in youtube_links_input.split(",")]
save_comments_from_links(youtube_links)

# Close the MongoDB connection
client.close()
