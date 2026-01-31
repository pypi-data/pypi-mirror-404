# pylint: skip-file
"""Host 主机, 用来监控设备端 secs服务发上来的数据, 然后处理后再发给工厂."""
import logging

from secsgem.hsms import HsmsMessage
from secsgem.secs import SecsStreamFunction
from secsgem import hsms, gem


class ActiveHost:
    """ActiveHost class."""

    def __init__(self, passive_ips: list[str]):
        """ActiveHost 构造函数.

        Args:
            passive_ips: 要监控设备 secs 服务的 ip 和 端口列表.
        """
        self.logger = logging.getLogger("ActiveHost")
        self.passive_ips = passive_ips
        self._host_handlers = {}
        self._create_gem_host_handler()

    def _create_gem_host_handler(self):
        """根据配置文件创建连接设备的客户端."""
        for equipment_ip_port in self.passive_ips:
            equipment_ip, port = equipment_ip_port.split(":")
            setting = hsms.HsmsSettings(
                address=equipment_ip,
                port=int(port),
                connect_mode=getattr(hsms.HsmsConnectMode, "ACTIVE"),
                device_type=hsms.DeviceType.HOST
            )
            host_handler = gem.GemHostHandler(setting)
            self._host_handlers[equipment_ip_port] = host_handler

    @property
    def host_handlers(self) -> dict[str, gem.GemHostHandler]:
        """监控设备 secs 服务的 GemHostHandler 实例字典."""
        return self._host_handlers

    def enable_host_handler(self):
        """启动监控设备 secs 服务的客户端"""
        for equipment_ip_port, host_handler in self._host_handlers.items():
            host_handler.enable()
            self.logger.info("已启动监控 %s 设备 secs 服务的 Active 客户端", equipment_ip_port)

    def get_host_handler(self, ip_port: str) -> gem.GemHostHandler:
        """获取监控设备 secs 服务的 GemHostHandler.

        Args:
            ip_port: 监控设备 secs 服务的 ip 和 端口.

        Returns:
            gem.GemHostHandler: 返回 gem.GemHostHandler.
        """
        return self._host_handlers[ip_port]

    def send_sf(self, sf_instance: SecsStreamFunction) -> list[HsmsMessage]:
        """给指定设备的 secs 服务下发流函数.

        Args:
            sf_instance: 要下发的流函数实例.

        Returns:
             list[HsmsMessage]: 返回设备端服务返回的 HsmsMessage 列表.
        """
        result_list = []
        for equipment_ip_port, host_handler in self._host_handlers.items():
            self.logger.info("已给设备 %s 下发流函数", equipment_ip_port)
            message = host_handler.send_and_waitfor_response(sf_instance)
            self.logger.info("设备 %s 已回复 %s", equipment_ip_port, f"s{message.header.stream}f{message.header.function}")
            result_list.append(message)
        return result_list