# pylint: skip-file
"""这个类是 host 端 secs passive 服务的实现, 继承了 PassiveServer 类."""
import threading
from typing import Callable

from secsgem.hsms import HsmsMessage
from secsgem.secs import functions

from passive_server import factory, passive_server


class HostPassive(passive_server.PassiveServer):
    """HostPassive class."""

    def __init__(self):
        """HostPassive 构造函数."""
        super().__init__(is_host=True)

        self._equipment_connect_state_dict = {}  # 所有设备的连接状态
        self.active_host = factory.get_active_host_instance(self.mysql_secs)
        self.active_host.logger.addHandler(self.file_handler)
        self._host_thread()

    @property
    def equipment_connect_state(self) -> bool:
        """所有设备是否已连接.

        Returns:
            bool: True -> 已连接所有设备, False -> 未连接所有设备.
        """
        is_all_connect = True
        for equipment_ip_port, equipment_handler in self.active_host.host_handlers.items():
            # noinspection PyUnresolvedReferences
            if equipment_handler.protocol.connection_state.current.value == 0:
                self._equipment_connect_state_dict[equipment_ip_port] = False
                self.logger.warning("%s 未连接!", equipment_ip_port)
                is_all_connect = False
            else:
                self._equipment_connect_state_dict[equipment_ip_port] = True
                self.logger.info("%s 已连接!", equipment_ip_port)

        return is_all_connect

    @property
    def equipment_connect_state_dict(self) -> dict[str, bool]:
        """所有设备的连接状态.

        Returns:
            dict[str, bool]: 返回所有设备的连接状态字典.
        """
        if self.equipment_connect_state:
            self.logger.info("所有设备均已连接")
        return self._equipment_connect_state_dict

    def _host_thread(self):
        """Host 电脑的线程."""
        self._set_on_sf()
        threading.Thread(target=self.active_host.enable_host_handler, daemon=True).start()

    def _set_on_sf(self):
        """设置 host 收到的流函回调."""
        for ip_port in self.active_host.passive_ips:
            for attribute_name in dir(self):
                if attribute_name.startswith("_customer_"):
                    func = getattr(self, attribute_name)
                    func_name = attribute_name.split("_customer_")[-1]
                    setattr(self.active_host.get_host_handler(ip_port), func_name, func)

    def _send_sf_to_equipment_passive(self, message: HsmsMessage):
        """Host passive 收到工厂下发的指令后下发给设备 secs 服务.

        Args:
            message: HsmsMessage 消息数据实例.
        """
        sf_instance = self.get_sf_instance(message)
        return getattr(self.active_host, f"send_sf")(sf_instance)

    def s02f41_pre(self, message: HsmsMessage, *_):
        """Host passive 收到工厂下发的 S2F41 给设备 secs 服务下发 S2F41 的操作.

        Args:
            message: HsmsMessage 消息数据实例.
        """
        return self.send_sf_pre_check(message)

    def s02f49_pre(self, message: HsmsMessage, *_):
        """Host passive 收到工厂下发的 S2F49 给设备 secs 服务下发 S2F49 的操作.

        Args:
            message: HsmsMessage 消息数据实例.
        """
        return self.send_sf_pre_check(message)

    def s03f17_pre(self, message: HsmsMessage, *_):
        """Host passive 收到工厂下发的 S3F17给设备 secs 服务下发 S3F17 的操作.

        Args:
            message: HsmsMessage 消息数据实例.
        """
        return self.send_sf_pre_check(message)

    def s07f03_pre(self, message: HsmsMessage, *_):
        """Host passive 收到工厂下发的 S07F03 给设备 secs 服务下发 S07F03 的操作.

        Args:
            message: HsmsMessage 消息数据实例.
        """
        return self.send_sf_pre_check(message)

    def s07f17_pre(self, message: HsmsMessage, *_):
        """Host passive 收到工厂下发的 S07F17 给设备 secs 服务下发 S07F17 的操作.

        Args:
            message: HsmsMessage 消息数据实例.
        """
        return self.send_sf_pre_check(message)

    def _customer__on_s05f01(self, *_) -> functions.SecsS05F02:
        """自定义的 _on_s0501 回调函数, 覆盖 GemHostHandler 下的 _on_s0501.

        Returns:
            SecsS06F12: 返回 SecsS05F02.
        """
        return self.stream_function(5, 2)(0)

    def _customer__on_s06f11(self, *_) -> functions.SecsS06F12:
        """自定义的 _on_s0611 回调函数, 覆盖 GemHostHandler 下的 _on_s0611.

        Returns:
            SecsS06F12: 返回 SecsS06F12.
        """
        return self.stream_function(6, 12)(0)

    def _customer_s05f01_pre(self, message: HsmsMessage, *_):
        """Host passive 收到设备上报的报警处理后上报给工厂.

        Args:
            message: HsmsMessage 消息数据实例.
        """
        s5f1_instance = self.get_sf_instance(message)
        threading.Thread(target=self.send_and_waitfor_response, args=(s5f1_instance,), daemon=True).start()

    def _customer_s06f11_pre(self, message: HsmsMessage, *_):
        """Host passive 收到设备上报的事件处理后上报给工厂.

        Args:
            message: HsmsMessage 消息数据实例.
        """
        data = self.get_receive_data_dict(message)
        s6f11_instance = self.get_sf_instance(message)
        event_id = data["CEID"]
        if event_received_pre := getattr(self, f"_on_event_{self.collection_events[event_id].name}", None):
            event_received_pre(event_id, data["RPT"])
        self.send_and_waitfor_response(s6f11_instance)

    def send_sf_to_equipment_passive(self, message: HsmsMessage) -> list[HsmsMessage]:
        """获取给设备 secs 服务发送指令的函数.

        Args:
            message: HsmsMessage 消息数据实例.

        Returns:
            list[HsmsMessage]: 存在未连接的设备直接返回空列表, 否则返回数据列表.
        """
        return self._send_sf_to_equipment_passive(message)

    def send_sf_pre_check(self, message: HsmsMessage, call_func: Callable = None) -> tuple[bool, int]:
        """Host 接收到工厂下发的流函数进行预检查, 检查通过后在下发给设备.

        Args:
            message: HsmsMessage 消息数据实例.
            call_func: 要执行的函数.

        Returns:
            tuple[bool, int]: 返回检查结果.
        """
        if self.equipment_connect_state:
            result_messages = self.send_sf_to_equipment_passive(message)
            for result_message in result_messages:  # 遍历所有的返回结果
                if (result_value := self.get_receive_data_dict(result_message)) not in [0, 4]:  # 不等于 0 或 4 说明失败了
                    return False, result_value

            if call_func:
                call_func(message)

            return True, 0
        return False, 7
