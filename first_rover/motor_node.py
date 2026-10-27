#!/usr/bin/env python3
'''
Description:
    This ROS 2 node subscribes to the user input to every node that is publishing to the motor_speed(topic) node. 
------
Publishing Topics:


------
Subscritption Topics:
    Subscribes to the user input.   
    motor_speed - std_msgs/Int32

Author:
Deniss Fjodorovs
Date: 20/10/26
'''
# Import rclpy (the ROS 2 Python library)
import rclpy
# From rclpy.node, import Node
from rclpy.node import Node
# From time, import sleep
from time import sleep
# From std_msgs.msg import Int32
from std_msgs.msg import Int32
import socket
import time

PICO_IP = "192.168.1.57"
PORT = 5005

# Create a class called MotorNode that inherits from Node
class MotorNode(Node):
    # Define __init__(self)
    def __init__(self):
        # Register this node with ROS 2 under the name 'motor_node'
        super().__init__("motor_node")

        # Open the serial connection to the Pico and store it on the node (self.ser),
        # so speed_callback can use it later


        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.speed = 0
        self.last_command = time.time()
        self.timer = self.create_timer(0.2, self.heartbeat_callback)
        # Listen to the "motor_speed" topic (Int32 messages).
        # Every time a message arrives, run speed_callback.
        # 10 = queue size: how many messages to hold if they arrive faster than we handle them.
        # When your command node runs create_publisher(..., "motor_speed", ...), 
        # ROS 2 effectively says “there’s now a topic called motor_speed.” 
        # When the motor node subscribes with the same name, ROS 2 connects the two. 
        # There’s no separate step where you create it.
        self.subscriber_1 = self.create_subscription(
            Int32,
            "motor_speed",
            self.speed_callback,
            10
        )

    def speed_callback(self, msg):
        # Turn the number into text with a newline, then into bytes for serial.
        # The newline matters: the Pico's readline() waits for the end of the line.
        self.last_command = time.time()
        self.speed = msg.data
        # Log the bytes being sent (ROS 2's version of print)
        self.get_logger().info(f"Speed: {self.speed}")

        # Send the bytes to the Pico through this node's serial connection.
        # write = send, self.ser = the open connection (not the port name),
        # self = this MotorNode object

    def heartbeat_callback(self):
        self.elapsed = time.time() - self.last_command
        if self.elapsed > 1:
            self.sock.sendto(b"0\n",(PICO_IP, PORT))
        else:
            self.sock.sendto(f"{self.speed}\n".encode(), (PICO_IP, PORT))





# Define a function called main()
def main(args=None):
    # Start ROS 2 with rclpy.init()
    rclpy.init(args=args)

    # Create a MotorNode and store it in a variable called node
    motor_node = MotorNode()

    # try:
    try:
        # keeps a node watiting for incoming messages. rclpy.spin() keeps it listening and runs the callback whenever one comes in.
        rclpy.spin(motor_node)
        # Keep the node running until Ctrl+C, using rclpy.spin(node)
    except KeyboardInterrupt:
        # Do nothing (just let the program move on to finally)
        pass    
    finally: #(runs no matter how the program ends):

        # Send 0 through node.ser so the motors stop

        motor_node.sock.sendto("0\n".encode(),(PICO_IP, PORT))


        # Close the serial port
        motor_node.sock.close()

        # Clean up the node with node.destroy_node()
        motor_node.destroy_node()
        # Shut down ROS 2 with rclpy.try_shutdown()
        rclpy.try_shutdown()

if __name__== "__main__":
    #Execute the main function if the script is run directly
    main()