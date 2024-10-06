from flask import Flask, render_template, Response
import cv2
import mysql.connector
import numpy as np

app = Flask(__name__)

# Database configuration
DB_CONFIG = {
    'user': 'your_username',        # Replace with your MySQL username
    'password': 'your_password',    # Replace with your MySQL password
    'host': 'localhost',            # Database host
    'database': 'animal_detection'   # Name of the database
}

# Load YOLO model and classes
yolo_net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
with open('coco.names', 'r') as f:
    yolo_classes = f.read().splitlines()

# Function to perform YOLO object detection on a frame
def perform_yolo_detection(frame):
    height, width, _ = frame.shape
    blob = cv2.dnn.blobFromImage(frame, 1/255, (320, 320), (0, 0, 0), swapRB=True, crop=False)
    yolo_net.setInput(blob)

    output_layers_names = yolo_net.getUnconnectedOutLayersNames()
    layer_outputs = yolo_net.forward(output_layers_names)

    boxes, confidences, class_ids = [], [], []
    for output in layer_outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.7:
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    detections = []
    for i in indexes.flatten():
        x, y, w, h = boxes[i]
        label = str(yolo_classes[class_ids[i]])
        confidence = confidences[i]
        detections.append((label, confidence))
        # Store detection in the database
        store_detection(label, confidence)

        # Draw bounding box
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(frame, f"{label} {round(confidence, 2)}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    return frame

def store_detection(object_label, confidence):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO detections (object, confidence, count) 
        VALUES (%s, %s, %s)
    ''', (object_label, confidence, 1))  # Assuming each detection is a count of 1
    conn.commit()
    cursor.close()
    conn.close()

def generate_frames():
    video_capture = cv2.VideoCapture(0)
    while True:
        success, frame = video_capture.read()
        if not success:
            break
        frame = perform_yolo_detection(frame)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
