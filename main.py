import cv2
import mediapipe as mp
import time
import math
from calcstack import Stack

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Define the calculator layout
calculator_layout = {
    '7': (100, 100), '8': (200, 100), '9': (300, 100), '/': (400, 100),'SQ': (500, 100),
    '4': (100, 200), '5': (200, 200), '6': (300, 200), '*': (400, 200),'^': (500, 200),
    '1': (100, 300), '2': (200, 300), '3': (300, 300), '-': (400, 300),
    '0': (200, 400), '=': (300, 400), '+': (400, 400), 'C': (100, 400)
}

# Function to draw the calculator layout
def draw_calculator(frame):
    for key, pos in calculator_layout.items():
        cv2.rectangle(frame, (pos[0] - 50, pos[1] - 50), (pos[0] + 50, pos[1] + 50), (0, 255, 0), 2)
        cv2.putText(frame, key, (pos[0] - 20, pos[1] + 20), cv2.FONT_HERSHEY_TRIPLEX,1,(0, 125, 255), 2)

# Function to check if a point is inside a button
def is_inside(pos, point):
    return pos[0] - 50 < point[0] < pos[0] + 50 and pos[1] - 50 < point[1] < pos[1] + 50
stack = Stack()
# Initialize the camera
cap = cv2.VideoCapture(0)

# Variables to store the calculator state
current_input = ""
last_key = None
key_pressed_time = 1.0
debounce_time = 1.5  # 0.5 seconds debounce time

# Define video writer
frame_width = int(cap.get(3))
frame_height = int(cap.get(4))
out = cv2.VideoWriter('virtual_calculator.avi', cv2.VideoWriter_fourcc(*'XVID'), 20, (frame_width, frame_height))
evalution = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)  # Flip the frame horizontally for a mirror view
    h, w, c = frame.shape
    
    # Convert the frame to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process the frame with MediaPipe Hands
    result = hands.process(rgb_frame)
    
    # Apply a color effect (grayscale)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    
    # Draw the calculator layout
    draw_calculator(frame)
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Get the tip of the index finger
            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            x = int(index_finger_tip.x * w)
            y = int(index_finger_tip.y * h)

            # Check if other fingers are closed
            fingers = [hand_landmarks.landmark[mp_hands.HandLandmark(i)] for i in range(4, 21, 4)]
            other_fingers_closed = all(finger.y > hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].y for finger in fingers)
            
            if not other_fingers_closed:
                # Draw a circle at the tip of the index finger
                cv2.circle(frame, (x, y), 10, (255, 0, 0), -1)
                
                # Check if the index finger tip is inside any button
                for key, pos in calculator_layout.items():
                    if is_inside(pos, (x, y)):
                        cv2.rectangle(frame, (pos[0] - 50, pos[1] - 50), (pos[0] + 50, pos[1] + 50), (180, 255, 204), 2)
                        
                        # Check debounce condition
                        if key != last_key or (time.time() - key_pressed_time) > debounce_time:
                            last_key = key
                            key_pressed_time = time.time()

                            # If the '=' button is pressed, evaluate the expression
                            if key == '=':
                                try:
                                    current_input = str(eval(str(stack)))
                                    cv2.putText(frame, current_input, (80, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (120, 0, 255), 2)
                                    evalution = 1
                                    stack.clear()
                                except:
                                    current_input = "Error"
                            
                            # If the 'C' button is pressed, clear the input
                            elif key == 'C':
                                current_input = ""
                                evalution = 3
                                stack.clear()
                            
                            # If the '√' button is pressed, compute the square root
                            elif key == 'SQ':
                                evalution = 0
                                try:
                                    stack.push("√")
                                except:
                                    current_input = "Error"
                            # For other buttons, add the key to the current input
                            else:
                                evalution = 0
                                if key.isdigit():
                                    stack.push(key)
                                elif  (not stack.is_empty()) and stack.peek() != key and stack.peek().isdigit():
                                    stack.push(key)
                            break
    
    # Display the current input
    if(evalution == 0):
        cv2.putText(frame, str(stack), (80, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (120, 0, 255), 2)
        current_input = ""
    elif evalution == 1:
        cv2.putText(frame, current_input, (80, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (120, 0, 255), 2)
    else:
        cv2.putText(frame, current_input, (80, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (120, 0, 255), 2)
    
    # Show the frame
    cv2.imshow("Virtual Calculator", frame)
    
    # Write the frame to the video file
    out.write(frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera and video writer, and close all OpenCV windows
cap.release()
out.release()
cv2.destroyAllWindows()
