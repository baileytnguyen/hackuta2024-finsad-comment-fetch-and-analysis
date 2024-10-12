import grpc
import comment_scam_detector_pb2
import comment_scam_detector_pb2_grpc
import time

def create_dummy_data():
    # Create a list of dummy comments
    comments = []
    
    comments.append(comment_scam_detector_pb2.Comment(
        user_id="user_1",
        username="john_doe",
        comment_text="This is a great product! Highly recommend it.",
        timestamp=int(time.time())  # Current Unix timestamp
    ))
    
    comments.append(comment_scam_detector_pb2.Comment(
        user_id="user_2",
        username="jane_smith",
        comment_text="I won a lottery! Click the link to claim your prize!",
        timestamp=int(time.time())  # Current Unix timestamp
    ))
    
    # Create a CommentThread
    comment_thread = comment_scam_detector_pb2.CommentThread(comments=comments)
    
    return comment_thread

def main():
    # Create a gRPC channel to connect to the server
    channel = grpc.insecure_channel('10.234.118.25:50051')  # Update with your server address if needed
    stub = comment_scam_detector_pb2_grpc.ScamDetectionServiceStub(channel)

    # Create dummy data
    comment_thread = create_dummy_data()
    
    # Create a request to send to the server
    request = comment_scam_detector_pb2.ScamDetectionRequest(thread=comment_thread)
    
    # Call the DetectScam method and get the response
    response = stub.DetectScam(request)
    
    # Print the response
    print("Scam Detection Result:")
    print(f"Is Scam: {response.is_scam}")
    print(f"Message: {response.message}")
    print(f"Confidence: {response.confidence}")

if __name__ == "__main__":
    main()