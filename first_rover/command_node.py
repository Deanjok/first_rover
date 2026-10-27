#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32

class CommandNode(Node):
    def __init__(self):
        super().__init__("command_node")
        self.publisher = self.create_publisher(
            Int32,
            "motor_speed",
            10
        )
    def send_speed(self, speed):
        msg = Int32()
        msg.data = speed
        self.publisher.publish(msg)
        self.get_logger().info(f"Speed is:{speed}")

def main(args=None):

    rclpy.init(args=args)

    command_node = CommandNode()

    try:
        while True:
            speed = int((input("Give me a speed: ")))
            command_node.send_speed(speed)
    except ValueError:
        print("You need to type a number!")
    except KeyboardInterrupt:
        command_node.send_speed(0)
    finally:
         command_node.destroy_node()
         rclpy.try_shutdown()

if __name__ == "__main__":
    main()