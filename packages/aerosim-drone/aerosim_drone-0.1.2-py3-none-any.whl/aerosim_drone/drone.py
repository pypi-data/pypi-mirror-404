import asyncio
import websockets
import sys
import json
import time

from aerosim_drone.commands.arm import Arm
from aerosim_drone.commands.land import Land
from aerosim_drone.commands.navigate import Navigate
from aerosim_drone.commands.navigate_global import NavigateGlobal
from aerosim_drone.commands.set_altitude import SetAltitude
from aerosim_drone.commands.set_attitude import SetAttitude
from aerosim_drone.commands.set_position import SetPosition
from aerosim_drone.commands.set_rates import SetRates
from aerosim_drone.commands.set_velocity import SetVelocity
from aerosim_drone.commands.set_yaw import SetYaw
from aerosim_drone.commands.set_yaw_rate import SetYawRate

COMMANDS_CHANNEL = 'commands'


class Drone:
    def __init__(self, host="localhost", port=8080):
        self.uri = f"ws://{host}:{port}"
        self._ws = None
        self._loop = None

    # ---------- connection ----------

    async def _connect_async(self):
        self._ws = await websockets.connect(self.uri)

    def connect(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        async def setup():
            await self._connect_async()
            asyncio.create_task(self._recv_loop())

        try:
            self._loop.run_until_complete(setup())
        except Exception as e:
            print(f"Connection error: {e}", file=sys.stderr)
            return

        self._loop.create_task(asyncio.sleep(0))

    async def _recv_loop(self):
        try:
            async for msg in self._ws:
                data = json.loads(msg)
                print("[TEXT]", data)
                # if data.get("channel") == "texts":
                #     print("[TEXT]", data)
        except Exception as e:
            print("[WS] recv error:", e)

    # def connect(self):
    #     self._loop = asyncio.new_event_loop()
    #     asyncio.set_event_loop(self._loop)
    #     try:
    #         self._loop.run_until_complete(self._connect_async())
    #     except Exception as e:
    #         print(f"Connection error: {e}", file=sys.stderr)
    #         sys.exit(1)

    def disconnect(self):
        async def _close():
            await self._ws.close()

        self._loop.run_until_complete(_close())
        self._loop.close()

    # ---------- private sender ----------

    def _send_websocket_data(self, payload, channel):
        async def _send():
            message = json.dumps({
                "channel": channel,
                "payload": payload,
            })
            print(message)
            await self._ws.send(message)

        self._loop.run_until_complete(_send())

    def _send_command(self, command):
        self._send_websocket_data({
            "model": "command",
            "type": command.name,
            "timestamp": int(time.time()),
            "data": command.getData()
        }, COMMANDS_CHANNEL)

    # ---------- Commands ----------

    def arm(self):
        self._send_command(Arm())

    def land(self):
        self._send_command(Land())

    def navigate(
            self,
            x: float,
            y: float,
            z: float,
            speed: float,
            frame_id: str = "map",
            auto_arm: bool = False
    ):
        """
        Fly to the designated point in a straight line.

        :param x: Coordinate x
        :param y: Coordinate y
        :param z:Coordinate z
        :param speed: Flight speed (setpoint speed) (m/s)
        :param frame_id: Coordinate system for values x, y, z and yaw. Example: map, body, aruco_map. Default value: map.
        :param auto_arm: Switch the drone to OFFBOARD and arm automatically (the drone will take off)
        :return:
        """
        self._send_command(
            Navigate(
                x=x,
                y=y,
                z=z,
                speed=speed,
                frame_id=frame_id,
                auto_arm=auto_arm
            )
        )

    def navigate_global(
            self,
            lat: float,
            lon: float,
            z: float,
            yaw: float,
            speed: float,
            frame_id: str = "map",
            auto_arm: bool = False
    ):
        self._send_command(
            NavigateGlobal(
                lat=lat,
                lon=lon,
                z=z,
                yaw=yaw,
                speed=speed,
                frame_id=frame_id,
                auto_arm=auto_arm
            )
        )

        def set_altitude(
                self,
                z: float,
                frame_id: str = "map",
        ):
            self._send_command(
                SetAltitude(
                    z=z,
                    frame_id=frame_id
                )
            )

        def set_attitude(
                self,
                roll: float,
                pitch: float,
                yaw: float,
                thrust: float,
                frame_id: str = "map",
                auto_arm: bool = False,
        ):
            self._send_command(
                SetAttitude(
                    roll=roll,
                    pitch=pitch,
                    yaw=yaw,
                    thrust=thrust,
                    frame_id=frame_id,
                    auto_arm=auto_arm,
                )
            )

        def set_position(
                self,
                x: float,
                y: float,
                z: float,
                frame_id: str = "map",
                auto_arm: bool = False,
        ):
            self._send_command(
                SetPosition(
                    x=x,
                    y=y,
                    z=z,
                    frame_id=frame_id,
                    auto_arm=auto_arm,
                )
            )

        def set_rates(
                self,
                roll_rate: float,
                pitch_rate: float,
                yaw_rate: float,
                thrust: float,
                auto_arm: bool = False,
        ):
            self._send_command(
                SetRates(
                    roll_rate=roll_rate,
                    pitch_rate=pitch_rate,
                    yaw_rate=yaw_rate,
                    thrust=thrust,
                    auto_arm=auto_arm,
                )
            )

        def set_velocity(
                self,
                vx: float,
                vy: float,
                vz: float,
                yaw: float,
                frame_id: str = "map",
                auto_arm: bool = False,
        ):
            self._send_command(
                SetVelocity(
                    vx=vx,
                    vy=vy,
                    vz=vz,
                    yaw=yaw,
                    frame_id=frame_id,
                    auto_arm=auto_arm,
                )
            )

        def set_yaw(
                self,
                yaw: float,
                frame_id: str = "map"
        ):
            self._send_command(
                SetYaw(
                    yaw=yaw,
                    frame_id=frame_id,
                )
            )

        def set_yaw_rate(
                self,
                yaw_rate: float,
                frame_id: str = "map"
        ):
            self._send_command(
                SetYawRate(
                    yaw_rate=yaw_rate,
                    frame_id=frame_id,
                )
            )
