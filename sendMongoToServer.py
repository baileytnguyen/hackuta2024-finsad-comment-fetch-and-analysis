from pymongo import MongoClient
import grpc
import comment_scam_detector_pb2
import comment_scam_detector_pb2_grpc

def send_data_to_grpc_server(threads):
    # Create a gRPC channel for algorithm
    algo_channel = grpc.insecure_channel('10.232.120.227:50051')  # Replace with your gRPC server address
    algo_stub = comment_scam_detector_pb2_grpc.ScamDetectionServiceStub(algo_channel)

    # Create a gRPC channel for LLM
    ai_channel = grpc.insecure_channel('10.232.123.50:50051')  # Replace with your gRPC server address
    ai_stub = comment_scam_detector_pb2_grpc.ScamDetectionServiceStub(ai_channel)

    for thread in threads:
        comments = []
        
        top_comment = thread.get('topComment')  # Extract top comment
        if top_comment:
            comments.append(comment_scam_detector_pb2.Comment(
                user_id="1",
                username=top_comment.get('author'),
                comment_text=top_comment.get('comment_text'),
                timestamp=top_comment.get('timestamp') # Current Unix timestamp
                )  
            )
        else:
            # Extract replies
            replies = thread.get('replies', [])  # Assuming replies are stored in an array called 'replies'
            for reply in replies:
                comments.append(comment_scam_detector_pb2.Comment(
                    user_id="2",
                    username=reply.get('author'),
                    comment_text=reply.get('comment_text'),
                    timestamp=reply.get('timestamp') # Current Unix timestamp
                    )  
                )

        # Create a CommentThread
        comment_thread = comment_scam_detector_pb2.CommentThread(comments=comments)
        
        # Create a request to send to the server
        request = comment_scam_detector_pb2.ScamDetectionRequest(thread=comment_thread)
        
        # Call the DetectScam method and get the response
        algo_response = algo_stub.DetectScam(request)
        ai_response = ai_stub.DetectScam(request)
        
        # Print the response
        print("Algo Scam Detection Result:")
        print(f"Is Scam: {algo_response.is_scam}")
        print(f"Message: {algo_response.message}")
        print(f"Confidence: {algo_response.confidence}")

        # Print the response
        print("AI Scam Detection Result:")
        print(f"Is Scam: {ai_response.is_scam}")
        print(f"Message: {ai_response.message}")
        print(f"Confidence: {ai_response.confidence}")

    algo_channel.close()  # Close the channel
    ai_channel.close()  # Close the channel

# MongoDB connection
mongo_uri = 'mongodb://localhost:27017/'  # Adjust as necessary
client = MongoClient(mongo_uri)
db = client['youtube_comments_database']  # Replace with your database name
collection = db['comments']  # Replace with your collection name

# Extract data from MongoDB
documents = list(collection.find())
client.close()  # Close the MongoDB connection

# Send the extracted documents to the gRPC server
send_data_to_grpc_server(documents)
