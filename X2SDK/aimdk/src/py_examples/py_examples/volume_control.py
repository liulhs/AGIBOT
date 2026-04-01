#!/usr/bin/env python3

import argparse

import rclpy
import rclpy.logging
from rclpy.node import Node

from aimdk_msgs.srv import GetVolume, PlayTts, SetVolume


SERVICE_WAIT_TIMEOUT_SEC = 2.0
CALL_TIMEOUT_SEC = 0.25
MAX_RETRIES = 8


def clamp_volume(volume):
    return max(0, min(100, int(volume)))


class VolumeControlClient(Node):
    def __init__(self):
        super().__init__('volume_control_client')

        self.get_volume_client = self.create_client(
            GetVolume, '/aimdk_5Fmsgs/srv/GetVolume')
        self.set_volume_client = self.create_client(
            SetVolume, '/aimdk_5Fmsgs/srv/SetVolume')
        self.play_tts_client = self.create_client(
            PlayTts, '/aimdk_5Fmsgs/srv/PlayTts')

        self._wait_for_service(self.get_volume_client, 'GetVolume')
        self._wait_for_service(self.set_volume_client, 'SetVolume')
        self._wait_for_service(self.play_tts_client, 'PlayTts')

    def _wait_for_service(self, client, service_label):
        while not client.wait_for_service(timeout_sec=SERVICE_WAIT_TIMEOUT_SEC):
            self.get_logger().info(
                f'⏳ {service_label} service unavailable, waiting...')

        self.get_logger().info(f'🟢 {service_label} service ready.')

    def _call_with_retry(self, client, request, stamp_path, label):
        future = None
        for attempt in range(MAX_RETRIES):
            stamp_path(request).stamp = self.get_clock().now().to_msg()
            future = client.call_async(request)
            rclpy.spin_until_future_complete(
                self, future, timeout_sec=CALL_TIMEOUT_SEC)

            if future.done():
                return future.result()

            self.get_logger().info(f'{label} retrying ... [{attempt}]')

        self.get_logger().error(f'❌ {label} timed out.')
        return None

    def get_volume(self):
        request = GetVolume.Request()
        response = self._call_with_retry(
            self.get_volume_client,
            request,
            lambda req: req.request.header,
            'GetVolume',
        )
        if response is None:
            return None

        if response.reponse.header.code != 0:
            self.get_logger().error(
                f'❌ GetVolume failed: code={response.reponse.header.code} '
                f'message={response.reponse.message}')
            return None

        return int(response.audio_volume)

    def set_volume(self, volume):
        request = SetVolume.Request()
        request.audio_volume = clamp_volume(volume)

        response = self._call_with_retry(
            self.set_volume_client,
            request,
            lambda req: req.request.header,
            'SetVolume',
        )
        if response is None:
            return None

        if response.reponse.header.code != 0:
            self.get_logger().error(
                f'❌ SetVolume failed: code={response.reponse.header.code} '
                f'message={response.reponse.message}')
            return None

        return int(response.audio_volume)

    def speak_volume(self, volume):
        request = PlayTts.Request()
        request.tts_req.text = f'Volume Set to {int(volume)} Percent'
        request.tts_req.domain = 'volume_control'
        request.tts_req.trace_id = 'volume_control'
        request.tts_req.is_interrupted = True
        request.tts_req.priority_weight = 0
        request.tts_req.priority_level.value = 6

        response = self._call_with_retry(
            self.play_tts_client,
            request,
            lambda req: req.header.header,
            'PlayTts',
        )
        if response is None:
            return False

        if not response.tts_resp.is_success:
            self.get_logger().error(
                f'❌ TTS failed: {response.tts_resp.error_message}')
            return False

        return True


def parse_args():
    parser = argparse.ArgumentParser(
        description='Adjust X2 volume and announce the resulting level.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    get_parser = subparsers.add_parser('get', help='Read the current volume.')
    get_parser.add_argument(
        '--speak', action='store_true', help='Also announce the current volume.')

    up_parser = subparsers.add_parser('up', help='Increase the volume.')
    up_parser.add_argument(
        'amount', nargs='?', type=int, default=10, help='Step size (default: 10).')

    down_parser = subparsers.add_parser('down', help='Decrease the volume.')
    down_parser.add_argument(
        'amount', nargs='?', type=int, default=10, help='Step size (default: 10).')

    set_parser = subparsers.add_parser('set', help='Set volume to an exact value.')
    set_parser.add_argument('value', type=int, help='Target volume (0-100).')

    return parser.parse_args()


def main(args=None):
    cli_args = parse_args()
    rclpy.init(args=args)
    node = None

    try:
        node = VolumeControlClient()

        current_volume = node.get_volume()
        if current_volume is None:
            raise RuntimeError('Unable to read current volume.')

        if cli_args.command == 'get':
            final_volume = current_volume
            node.get_logger().info(f'Current volume: {final_volume}%')
            if cli_args.speak:
                node.speak_volume(final_volume)
            return

        if cli_args.command == 'up':
            target_volume = current_volume + abs(cli_args.amount)
        elif cli_args.command == 'down':
            target_volume = current_volume - abs(cli_args.amount)
        else:
            target_volume = cli_args.value

        final_volume = node.set_volume(target_volume)
        if final_volume is None:
            raise RuntimeError('Unable to set volume.')

        node.get_logger().info(
            f'Volume changed from {current_volume}% to {final_volume}%')
        node.speak_volume(final_volume)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        rclpy.logging.get_logger('main').error(
            f'Program exited with exception: {exc}')
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
