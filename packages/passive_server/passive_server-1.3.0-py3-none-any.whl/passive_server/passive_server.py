# pylint: skip-file
"""Passive Server 基类, 设备端 passive 服务和 host 端 passive server 都要继承这个类.

这个类里包含了 PassiveEquipment 和 HostEquipment 共用的方法.
"""
import asyncio
import copy
import json
import logging
import threading
import socket
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from typing import Union, Optional, Callable

from secsgem.common import Message
from secsgem.gem import GemEquipmentHandler, DataValue, CollectionEventLink
from secsgem.hsms import HsmsMessage
from secsgem.secs.data_items import ACKC10, tiack
from secsgem.secs import functions, variables, SecsStreamFunction, data_items
from socket_cyg.socket_server_asyncio import CygSocketServerAsyncio

from passive_server import secs_config, factory, common_func, models_class
from passive_server.display_log import send_post


class PassiveServer(GemEquipmentHandler):
    """PassiveServer class."""

    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    logging.basicConfig(level=logging.INFO, encoding="UTF-8", format=LOG_FORMAT)

    def __init__(self, mysql_host: str = "127.0.0.1", database_name: str = "big_beauty", user_name: str = "root", is_host: bool = False):
        """PassiveServer 构造函数.

        Args:
            mysql_host: 配置数据所在的数据库 ip 地址.
            database_name: 所在数据库名称.
            user_name: 数据库用户名.
            is_host: 是否是 host.
        """
        self.mysql_secs = factory.get_mysql_instance(mysql_host, database_name, user_name)
        self.is_host = is_host
        self.socket_server_secs = factory.get_socket_server(self.mysql_secs, "socket_port_secs")
        self.socket_server_low = factory.get_socket_server(self.mysql_secs, "socket_port_low")

        super().__init__(settings=factory.get_hsms_setting(self.mysql_secs))
        self._collection_events = {}  # 清空所有的定义事件
        self.logger = logging.getLogger(__name__)  # handler_passive 日志器
        self._file_handler = None  # 保存日志的处理器
        self._initial_log_config()
        self._monitor_socket_thread()

        self._initial_equipment_constant()
        self._initial_status_variable()
        self._initial_data_value()
        self._initial_remote_command()
        self._initial_alarm()
        self._enabled_alarm()
        self._initial_event()  # 加载所有页面定义的事件, 关联自定义的报告
        self._update_registered_reports()  # 更新工厂上次注册的报告进行注册
        self._update_registered_collection_events()  # 更新工厂上次注册的事件

        self.enable_passive_server()  # 启动 passive 服务

    def __start_monitor_socket_thread(self, control_instance: CygSocketServerAsyncio, func: Callable):
        """启动 socket 服务.

        Args:
            control_instance: CygSocketServerAsyncio 实例.
            func: 执行操作的函数.
        """
        control_instance.operations_return_data = func
        threading.Thread(target=self.run_socket_server, args=(control_instance,), daemon=True).start()

    def __update_recipe_info(self, message: HsmsMessage):
        """添加或更新配方信息.

        Args:
            message: 下发的配方信息.
        """
        data = self.get_receive_data_dict(message)
        if "CCODE" in data:
            model_name = data.get("MDLN", "")
            softer_version = data.get("SOFTREV", "")
            self.logger.info("model_name: %s, softer_version: %s", model_name, softer_version)
            recipe_body = json.dumps(data.get("CCODE", [])).encode("UTF-8")
        else:
            recipe_body = data.get("PPBODY", "").encode("UTF-8")

        recipe_name = data.get("PPID", "")
        add_data = [{"recipe_name": recipe_name, "recipe_body": recipe_body}]
        recipe_name_filter = {"recipe_name": recipe_name}
        if recipe_name not in self.recipe_names:
            self.mysql_secs.add_data(models_class.RecipeInfo, add_data)
            return
        self.mysql_secs.update_data(
            models_class.RecipeInfo, {"recipe_body": recipe_body}, recipe_name_filter
        )

    def __get_recipe_info(self, recipe_name: str) -> str:
        """获取配方信息.

        Args:
            recipe_name: 配方名称.

        Returns:
            str: 获取配方信息.
        """
        recipe_info_list = self.mysql_secs.query_data(models_class.RecipeInfo, {"recipe_name": recipe_name})
        if recipe_info_list:
            recipe_body = recipe_info_list[-1]["recipe_body"].decode("UTF-8")
            return recipe_body
        return ""

    def _monitor_socket_thread(self):
        """监控 socket 的线程."""
        self.__start_monitor_socket_thread(self.socket_server_secs, self.operate_func_socket)
        self.__start_monitor_socket_thread(self.socket_server_low, self.operate_func_socket)

    def _update_registered_reports(self):
        """加载上次工厂注册的报告."""
        define_reports = secs_config.get_define_report(self.mysql_secs)
        for define_report in define_reports:
            self.registered_reports.update(define_report)

    def _update_registered_collection_events(self):
        """加载上次工厂注册的事件."""
        registered_events = secs_config.get_event_link_report(self.mysql_secs)
        for registered_event in registered_events:
            self.registered_collection_events.update(registered_event)

    def _enabled_alarm(self):
        """启用工厂已经启用的报警, 如果定义的启用报警是空列表则启用所有报警."""
        enabled_alarm_list = secs_config.get_enabled_alarm(self.mysql_secs)
        for alarm_id, alarm_instance in self.alarms.items():
            if alarm_id in enabled_alarm_list or not enabled_alarm_list:
                alarm_instance.enabled = True

    def _initial_log_config(self) -> None:
        """日志配置."""
        common_func.create_log_dir()
        self.protocol.communication_logger.addHandler(self.file_handler)  # secs 日志保存到统一文件
        self.logger.addHandler(self.file_handler)  # handler_passive 日志保存到统一文件
        self.socket_server_secs.logger.addHandler(self.file_handler)

    def _initial_status_variable(self):
        """加载定义好的 sv."""
        status_variables = secs_config.get_sv_list(self.mysql_secs)
        for status_variable in status_variables:
            self.status_variables.update(status_variable)
            if 513 in status_variable:  # 更新 model name
                self.model_name = status_variable[513].value
            if 514 in status_variable:   # 更新 softer version
                self.software_version = status_variable[514].value

    def _initial_data_value(self):
        """加载定义好的 data value."""
        data_values = secs_config.get_dv_list(self.mysql_secs)
        for data_value in data_values:
            self.data_values.update(data_value)

    def _initial_equipment_constant(self):
        """加载定义好的常量."""
        equipment_consts = secs_config.get_ec_list(self.mysql_secs)
        for equipment_const in equipment_consts:
            self.equipment_constants.update(equipment_const)

    def _initial_event(self):
        """加载定义好的事件."""
        events = secs_config.get_event_list(self.mysql_secs)
        for event in events:
            self.collection_events.update(event)

    def _initial_remote_command(self):
        """加载定义好的远程命令."""
        remote_commands = secs_config.get_remote_command_list(self.mysql_secs)
        for remote_command in remote_commands:
            self.remote_commands.update(remote_command)

    def _initial_alarm(self):
        """加载定义好的报警."""
        alarms = secs_config.get_alarm_list(self.mysql_secs)
        for alarm in alarms:
            self.alarms.update(alarm)

    @property
    def factory_connect_state(self) -> bool:
        """工厂连接状态.

        Returns:
            bool: True -> 工厂已连接, False -> 工厂未连接.
        """
        # noinspection PyUnresolvedReferences
        return self.protocol.connection_state.current.value != 0

    @property
    def recipe_names(self) -> list:
        """返回当前所有的配方名称.

        Returns:
            list: 返回当前所有的配方名称.
        """
        recipe_list = self.mysql_secs.query_data(models_class.RecipeInfo)
        return [recipe["recipe_name"] for recipe in recipe_list]

    @property
    def file_handler(self) -> TimedRotatingFileHandler:
        """设置保存日志的处理器, 每隔 24h 自动生成一个日志文件.

        Returns:
            TimedRotatingFileHandler: 返回 TimedRotatingFileHandler 日志处理器.
        """
        if self._file_handler is None:
            self._file_handler = factory.get_time_rotating_handler()
            self._file_handler.namer = common_func.custom_log_name
            self._file_handler.setFormatter(logging.Formatter(self.LOG_FORMAT))
        return self._file_handler

    @staticmethod
    def run_socket_server(server_instance: CygSocketServerAsyncio):
        """运行 socket 服务端.

        Args:
            server_instance: CygSocketServerAsyncio 实例对象.
        """
        asyncio.run(server_instance.run_socket_server())

    @staticmethod
    def send_data_to_socket_server(ip: str, port: int, data: str):
        """向服务端发送数据.

        Args:
            ip: Socket 服务端 ip.
            port: Socket 服务端 port.
            data: 要发送的数据.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))
        sock.sendall(data.encode("UTF-8"))

    @staticmethod
    def display_equipment_log(sf_str: str, log_content: str):
        """向页面发送设备日志数据."""
        send_post("equipment_secs_data", {"title": sf_str, "data": log_content})

    @staticmethod
    def display_factory_log(sf_str: str, log_content: str):
        """向页面发送工厂日志数据."""
        send_post("factory_secs_data", {"title": sf_str, "data": log_content})

    def enable_passive_server(self):
        """启动 passive 服务."""
        self.enable()  # 打开 passive 服务, 等待 active 连接
        self.logger.info("Passive 服务已启动, 地址: %s %s!", self.settings.address, self.settings.port)

    def get_sv_or_dv_value_with_id(self, sv_or_dv_id: int) -> Union[int, bool, float, str, list]:
        """根据 sv id 或 dv id 获取 sv 或 dv 值.

        Returns:
            Union[int, bool, float, str, list]: 返回 sv 或 dv 值.
        """
        if sv_or_dv_id in self.status_variables:
            return self.get_sv_value_with_id(sv_or_dv_id)
        return self.get_dv_value_with_id(sv_or_dv_id)

    def get_sv_or_dv_value_with_id_from_database(self, variable_id: int) -> Union[int, bool, float, str, list]:
        """根据名称从数据库里获取 sv 或者 dv 值.

        Args:
            variable_id: 变量 id.

        Returns:
            Union[int, bool, float, str, list]: 数据库里变量的值.
        """
        if variable_id in self.status_variables:
            return self.get_sv_value_with_name_from_database(self.status_variables[variable_id].name)
        return self.get_dv_value_with_name_from_database(self.data_values[variable_id].name)

    def set_sv_or_dv_value_with_id(self, sv_or_dv_id: int, value: Union[str, int, float, list], is_save: bool = True):
        """设置指定 sv 或 dv 变量的值.

        Args:
            sv_or_dv_id : 变量名称.
            value: 要设定的值.
            is_save: 是否更新数据库, 默认不更新.
        """
        if sv_or_dv_id in self.status_variables:
            self.set_sv_value_with_id(sv_or_dv_id, value, is_save)
        if sv_or_dv_id in self.data_values:
            self.set_dv_value_with_id(sv_or_dv_id, value, is_save)

    def set_sv_value_with_name(self, sv_name: str, sv_value: Union[str, int, float, list], is_save: bool = True):
        """设置指定 sv 变量的值.

        Args:
            sv_name : 变量名称.
            sv_value: 要设定的值.
            is_save: 是否更新数据库, 默认不更新.
        """
        if sv_instance := self.status_variables.get(self.get_sv_id_with_name(sv_name)):
            sv_instance.value = sv_value
            self.logger.info("设置 sv 值, %s = %s", sv_instance.name, sv_value)
        if is_save:
            filter_data = {"sv_name": sv_name}
            update_data = {"value": sv_value}
            self.mysql_secs.update_data(models_class.SvList, update_data, filter_data)

    def set_dv_value_with_name(self, dv_name: str, dv_value: Union[str, int, float, list], is_save: bool = True):
        """设置指定 dv 变量的值.

        Args:
            dv_name : 变量名称.
            dv_value: 要设定的值.
            is_save: 是否更新数据库, 默认不更新.
        """
        if dv_instance := self.data_values.get(self.get_dv_id_with_name(dv_name)):
            dv_instance.value = dv_value
            self.logger.info("设置 dv 值, %s = %s", dv_instance.name, dv_value)
        if is_save:
            filter_data = {"dv_name": dv_name}
            update_data = {"value": dv_value}
            self.mysql_secs.update_data(models_class.DvList, update_data, filter_data)

    def set_ec_value_with_name(self, ec_name: str, ec_value: Union[str, int, float, list], is_save: bool = True):
        """设置指定 ec 变量的值.

        Args:
            ec_name : 变量名称.
            ec_value: 要设定的值.
            is_save: 是否更新数据库, 默认不更新.
        """
        if ec_instance := self.data_values.get(self.get_ec_id_with_name(ec_name)):
            ec_instance.value = ec_value
            self.logger.info("设置 ec 值, %s = %s", ec_instance.name, ec_value)
        if is_save:
            filter_data = {"ec_name": ec_name}
            update_data = {"value": ec_value}
            self.mysql_secs.update_data(models_class.DvList, update_data, filter_data)

    def set_sv_value_with_id(self, sv_id: int, sv_value: Union[str, int, float, list], is_save: bool = True):
        """设置指定 sv 变量的值.

        Args:
            sv_id : 变量名称.
            sv_value: 要设定的值.
            is_save: 是否更新数据库, 默认不更新.
        """
        if sv_instance := self.status_variables.get(sv_id):
            sv_instance.value = sv_value
            self.logger.info("设置 sv 值, %s = %s", sv_instance.name, sv_value)
        if is_save:
            filter_data = {"sv_id": sv_id}
            update_data = {"value": sv_value}
            self.mysql_secs.update_data(models_class.SvList, update_data, filter_data)

    def set_dv_value_with_id(self, dv_id: int, dv_value: Union[str, int, float, list], is_save: bool = True):
        """设置指定 dv 变量的值.

        Args:
            dv_id: dv 变量 id.
            dv_value: 要设定的值.
            is_save: 是否更新数据库, 默认不更新.
        """
        if dv_instance := self.data_values.get(dv_id):
            dv_instance.value = dv_value
            self.logger.info("设置 dv 值, %s = %s", dv_instance.name, dv_value)
        if is_save:
            filter_data = {"dv_id": dv_id}
            update_data = {"value": dv_value}
            self.mysql_secs.update_data(models_class.DvList, update_data, filter_data)

    def set_ec_value_with_id(self, ec_id: int, ec_value: Union[str, int, float, list], is_save: bool = False):
        """设置指定 ec 变量的值.

        Args:
            ec_id: dv 变量 id.
            ec_value: 要设定的值.
            is_save: 是否更新数据库, 默认不更新.
        """
        if ec_instance := self.equipment_constants.get(ec_id):
            ec_instance.value = ec_value
            self.logger.info("设置 ec 值, %s = %s", ec_instance.name, ec_value)
        if is_save:
            filter_data = {"ec_id": ec_id}
            update_data = {"value": ec_value}
            self.mysql_secs.update_data(models_class.EcList, update_data, filter_data)

    def get_sv_value_with_id(self, sv_id: int, save_log: bool = True) -> Optional[Union[int, str, bool, list, float]]:
        """根据变量 sv 名获取变量 sv 值.

        Args:
            sv_id: 变量 id.
            save_log: 是否保存日志, 默认保存.

        Returns:
            Optional[Union[int, str, bool, list, float]]: 返回对应变量的值.
        """
        if sv_instance := self.status_variables.get(sv_id):
            sv_value = sv_instance.value
            if save_log:
                self.logger.info("当前 sv %s = %s", sv_instance.name, sv_value)
            return sv_instance.value
        return None

    def get_dv_value_with_id(self, dv_id: int, save_log: bool = True) -> Optional[Union[int, str, bool, list, float]]:
        """根据变量 dv id 取变量 dv 值..

        Args:
            dv_id: dv id.
            save_log: 是否保存日志, 默认保存.

        Returns:
            Optional[Union[int, str, bool, list, float]]: 返回对应 dv 变量的值.
        """
        if dv_instance := self.data_values.get(dv_id):
            dv_value = dv_instance.value
            if save_log:
                self.logger.info("当前 dv %s = %s", dv_instance.name, dv_value)
            return dv_value
        return None

    def get_sv_value_with_name(self, sv_name: str, save_log: bool = True) -> Optional[Union[int, str, bool, list, float]]:
        """根据变量 sv name 取变量 sv 值..

        Args:
            sv_name: sv id.
            save_log: 是否保存日志, 默认保存.

        Returns:
            Optional[Union[int, str, bool, list, float]]: 返回对应 sv 变量的值.
        """
        if sv_instance := self.status_variables.get(self.get_sv_id_with_name(sv_name)):
            sv_value = sv_instance.value
            if save_log:
                self.logger.info("当前 sv %s = %s", sv_instance.name, sv_value)
            return sv_value
        return None

    def get_dv_value_with_name(self, dv_name: str, save_log: bool = True) -> Optional[Union[int, str, bool, list, float]]:
        """根据变量 name 获取取变量 dv 值.

        Args:
            dv_name: dv id.
            save_log: 是否保存日志, 默认保存.

        Returns:
            Optional[Union[int, str, bool, list, float]]: 返回对应 dv 变量的值.
        """
        if dv_instance := self.data_values.get(self.get_dv_id_with_name(dv_name)):
            dv_value = dv_instance.value
            if save_log:
                self.logger.info("当前 dv %s = %s", dv_instance.name, dv_value)
            return dv_value
        return None

    def get_sv_value_with_name_from_database(self, sv_name: str, save_log: bool = True) -> Optional[Union[int, str, bool, list, float]]:
        """根据变量名称获取数据库里面 sv 的值.

        Args:
            sv_name: sv name.
            save_log: 是否保存日志, 默认保存.

        Returns:
            Optional[Union[int, str, bool, list, float]]: 返回数据库里对应 sv 变量的值.
        """
        sv_info_list = self.mysql_secs.query_data(models_class.SvList, {"sv_name": sv_name})
        if sv_info := sv_info_list[0]:
            sv_value = sv_info["value"]
            sv_value = common_func.parse_value(sv_value, sv_info["value_type"])
            if save_log:
                self.logger.info("数据库里当前 sv %s = %s", sv_name, sv_value)
            return sv_value
        return None

    def get_dv_value_with_name_from_database(self, dv_name: str, save_log: bool = True) -> Optional[Union[int, str, bool, list, float]]:
        """根据变量名称获取数据库里面 dv 的值.

        Args:
            dv_name: dv name.
            save_log: 是否保存日志, 默认保存.

        Returns:
            Optional[Union[int, str, bool, list, float]]: 返回数据库里对应 dv 变量的值.
        """
        dv_info_list = self.mysql_secs.query_data(models_class.DvList, {"dv_name": dv_name})
        if dv_info := dv_info_list[0]:
            dv_value = dv_info["value"]
            dv_value = common_func.parse_value(dv_value, dv_info["value_type"])
            if save_log:
                self.logger.info("数据库里当前 dv %s = %s", dv_name, dv_value)
            return dv_value
        return None

    def get_ec_value_with_name(self, ec_name: str, save_log: bool = True) -> Optional[Union[int, str, bool, list, float]]:
        """根据变量 ec name 取变量 ec 值..

        Args:
            ec_name: dv id.
            save_log: 是否保存日志, 默认保存.

        Returns:
            Optional[Union[int, str, bool, list, float]]: 返回对应 ec 变量的值.
        """
        if ec_instance := self.equipment_constants.get(self.get_ec_id_with_name(ec_name)):
            ec_value = ec_instance.value
            if save_log:
                self.logger.info("当前 ec %s = %s", ec_instance.name, ec_value)
            return ec_value
        return None

    def get_dv_id_with_name(self, dv_name: str) -> Optional[int]:
        """根据 dv name 获取 dv id.

        Args:
            dv_name: dv 名称.

        Returns:
            Optional[int]: dv id 或者 None.
        """
        for dv_id, dv_instance in self.data_values.items():
            if dv_instance.name == dv_name:
                return dv_id
        return None

    def get_sv_id_with_name(self, sv_name: str) -> Optional[int]:
        """根据 sv name 获取 sv id.

        Args:
            sv_name: sv 名称.

        Returns:
            Optional[int]: sv id 或者 None.
        """
        for sv_id, sv_instance in self.status_variables.items():
            if sv_instance.name == sv_name:
                return sv_id
        return None

    def get_ec_id_with_name(self, ec_name: str) -> Optional[int]:
        """根据 ec name 获取 ec id.

        Args:
            ec_name: ec 名称.

        Returns:
            Optional[int]: ec id 或者 None.
        """
        for ec_id, ec_instance in self.equipment_constants.items():
            if ec_instance.name == ec_name:
                return ec_id
        return None

    def get_ec_value_with_id(self, ec_id: int, save_log: bool = True) -> Optional[Union[int, str, bool, list, float]]:
        """根据常量名获取常量值.

        Args:
            ec_id: 常量 id.
            save_log: 是否保存日志, 默认保存.

        Returns:
            Optional[Union[int, str, bool, list, float]]: 返回对应常量的值.
        """
        if ec_instance := self.equipment_constants.get(ec_id):
            ec_value = ec_instance.value
            if save_log:
                self.logger.info("当前 ec %s = %s", ec_instance.name, ec_value)
            return ec_value
        return None

    def get_sv_name_with_id(self, sv_id: int) -> Optional[str]:
        """根据 sv id 获取 sv name.

        Args:
            sv_id: sv id.

        Returns:
            str: sv name.
        """
        if sv := self.status_variables.get(sv_id):
            return sv.name
        return None

    def get_dv_name_with_id(self, dv_id: int) -> Optional[str]:
        """根据 dv id 获取 dv name.

        Args:
            dv_id: dv id.

        Returns:
            str: dv name.
        """
        if dv := self.data_values.get(dv_id):
            return dv.name
        return None

    def get_ec_name_with_id(self, ec_id: int) -> Optional[str]:
        """根据 ec id 获取 ec name.

        Args:
            ec_id: ec id.

        Returns:
            str: ec name.
        """
        if ec := self.equipment_constants.get(ec_id):
            return ec.name
        return None

    def get_receive_data_dict(self, message: Message) -> Union[dict, int]:
        """获取收到到流函数数据字典.

        Args:
            message: Message 实例.

        Returns:
            Union[dict, int]: 返回收到到流函数数据字典。
        """
        sf_instance = self.decode_message(message)
        return sf_instance.get()

    def get_sf_instance(self, message: Message) -> SecsStreamFunction:
        """获取收到的流函数实例.

        Args:
            message: Message 实例.

        Returns:
            SecsStreamFunction: 返回流函数实例。
        """
        return self.decode_message(message)

    def send_s6f11(self, event_id: Union[int, str]):
        """给工厂发送S6F11事件.

        Args:
            event_id: 事件 id, 事件 id 是 int, 事件名称是 str.
        """
        if isinstance(event_id, str):
            event_id = secs_config.get_event_id_with_name(self.mysql_secs, event_id)
        if event_id and event_id in self.registered_collection_events:
            self.trigger_collection_events(event_id)
        else:
            if event_id and secs_config.get_event_state(self.mysql_secs, event_id):
                threading.Thread(target=self.collection_event_sender_customer, args=(event_id,), daemon=True).start()

    def collection_event_sender_customer(self, event_id: int):
        """设备发送事件给 Host, 不是工厂定义的事件报告, 是自定义的.

        Args:
            event_id: 事件 id.
        """
        reports = []
        event = self.collection_events.get(event_id)
        # noinspection PyUnresolvedReferences
        link_reports = event.link_reports
        for report_id, sv_or_dv_ids in link_reports.items():
            variable_list = []
            for sv_or_dv_id in sv_or_dv_ids:
                if sv_or_dv_id in self.status_variables:
                    sv_or_dv_instance = self.status_variables.get(sv_or_dv_id)
                else:
                    sv_or_dv_instance = self.data_values.get(sv_or_dv_id)
                if issubclass(sv_or_dv_instance.value_type, variables.Array):
                    # noinspection PyUnresolvedReferences
                    value = variables.Array(sv_or_dv_instance.base_value_type, sv_or_dv_instance.value)
                else:
                    value = sv_or_dv_instance.value_type(sv_or_dv_instance.value)
                variable_list.append(value)
            reports.append({"RPTID": variables.U4(report_id), "V": variable_list})

        self.send_and_waitfor_response(
            self.stream_function(6, 11)({"DATAID": 1, "CEID": event.ceid, "RPT": reports})
        )

    def _on_s02f17(self, *args) -> functions.SecsS02F18:
        """获取设备时间.

        Args:
            handler: handler the message was received on
            message: complete message received

        Returns:
            SecsS02F18: SecsS02F18 实例.
        """
        self.logger.info("收到的参数是: %s", args)
        current_time_str = datetime.now().strftime("%Y%m%d%H%M%S%C")
        return self.stream_function(2, 18)(current_time_str)

    def _on_s02f31(self, *args) -> functions.SecsS02F32:
        """设置设备时间.

        Args:
            handler: handler the message was received on
            message: complete message received

        Returns:
            SecsS02F32: 返回 SecsS02F32 实例.
        """
        parser_result = self.get_receive_data_dict(args[1])
        date_time_str = parser_result
        if len(date_time_str) not in (14, 16):
            self.logger.info("时间格式错误: %s 不是14或16个数字", date_time_str)
            return self.stream_function(2, 32)(tiack.TIACK.TIME_SET_FAIL)
        current_time_str = datetime.now().strftime("%Y%m%d%H%M%S%C")
        self.logger.info("当前时间: %s", current_time_str)
        self.logger.info("设置时间: %s", date_time_str)
        status = common_func.set_date_time(date_time_str)
        current_time_str = datetime.now().strftime("%Y%m%d%H%M%S%C")
        if status:
            self.logger.info(f"设置成功, 当前时间: %s", current_time_str)
            ti_ack = tiack.TIACK.ACK
        else:
            self.logger.info("设置失败, 当前时间: %s", current_time_str)
            ti_ack = tiack.TIACK.TIME_SET_FAIL
        return self.stream_function(2, 32)(ti_ack)

    def _on_s02f35(self, *args) -> functions.SecsS02F36:
        """将报告和事件关联.

        Args:
            handler: handler the message was received on
            message: complete message received

        Returns:
            SecsS02F36: 返回 SecsS02F36 实例.
        """
        function = self.decode_message(args[-1])
        lrack = data_items.LRACK.ACK

        for event in function.DATA:
            # 如果是 host 要检查事件是否存在
            if self.is_host and event.CEID.get() not in self._collection_events:
                lrack = data_items.LRACK.CEID_UNKNOWN
            for rptid in event.RPTID:
                # 判断事件是否注册
                if event.CEID.get() in self._registered_collection_events:
                    collection_event = self._registered_collection_events[event.CEID.get()]
                    # 判断报告是否已关联此事件
                    if rptid.get() in collection_event.reports:
                        lrack = data_items.LRACK.CEID_LINKED

                # 判断报告是否已注册
                if rptid.get() not in self._registered_reports:
                    lrack = data_items.LRACK.RPTID_UNKNOWN

        if lrack == 0:
            for event in function.DATA:
                # 判断事件是否存在, 存在则进行报告关联
                if (event_id := event.CEID.get()) in self.collection_events:
                    if not event.RPTID:  # 事件未关联报告
                        if event_id in self._registered_collection_events:
                            del self._registered_collection_events[event_id]  # 删除注册事件
                    else:  # 事件关联报告
                        if event_id in self._registered_collection_events:  # 事件已注册
                            collection_event = self._registered_collection_events[event_id]
                            for rptid in event.RPTID.get():  # 添加报告
                                collection_event.reports.append(rptid)
                        else:  # 事件未注册, 进行事件注册并关联报告
                            self._registered_collection_events[event_id] = CollectionEventLink(
                                self._collection_events[event_id], event.RPTID.get()
                            )

        return self.stream_function(2, 36)(lrack)

    def _on_s02f37(self, *args):
        """Handle Stream 2, Function 37, 启用停用事件.

        Args:
            handler: handler the message was received on.
            message: complete message received.
        """
        function = self.decode_message(args[-1])
        ceed, event_list = function.CEED.get(), function.CEID.get()
        erack = data_items.ERACK.ACCEPTED
        if ceed and event_list:  # 先判断要启用的事件是否注册, 若未注册则关联空报告
            add_data = []
            for event_id, event_instance in self.collection_events.items():
                if event_id not in self.registered_collection_events:  # 事件未注册关联空报告
                    self.registered_collection_events[event_id] = CollectionEventLink(event_instance, [])
                    add_data.append({"event_id": event_id, "state": 1})
            self.mysql_secs.add_data(models_class.ReportLinkEvent, add_data)

        if not self._set_ce_state(ceed, event_list):
            erack = data_items.ERACK.CEID_UNKNOWN

        return self.stream_function(2, 38)(erack)

    def _on_s02f49(self, *args) -> functions.SecsS02F50:
        """接收到工厂下发的 S02F49.

        Args:
            handler: handler the message was received on.
            message: complete message received.

        Returns:
            SecsS02F50: 返回 SecsS02F50 实例.
        """
        receive_data = self.get_receive_data_dict(args[1])
        self.logger.info("收到的 S2F49 数据是: %s", receive_data)
        return  self.stream_function(2, 50)({"HCACK": 0, "PARAMS": []})

    def _on_s03f17(self, *args) -> functions.SecsS03F18:
        """接收到工厂下发的 S03F17.

        Args:
            handler: handler the message was received on
            message: complete message received

        Returns:
            SecsS03F18: 返回 SecsS03F18 实例.
        """
        receive_data = self.get_receive_data_dict(args[-1])
        self.logger.info("收到的 S3F7 数据是: %s", receive_data)
        return self.stream_function(3, 18)({"CAACK": 0, "PARAMS": []})

    def _on_s05f03(self, *args) -> functions.SecsS05F04:
        """接收到工厂下发的 S05F03, 启用或停用报警, 如果是 alids 空列表则对所有报警进行操作.

        Args:
            handler: handler the message was received on.
            message: complete message received.

        Returns:
            SecsS05F04: 返回 SecsS05F04 实例.
        """
        s5f3_instance = self.get_sf_instance(args[-1])
        result = data_items.ACKC5.ACCEPTED
        alids = s5f3_instance.ALID.get()
        if isinstance(alids, int):
            alids = [alids]

        if not alids:
            for alair_id, alarm_instance in self.alarms.items():
                alarm_instance.enabled = s5f3_instance.ALED.get() == data_items.ALED.ENABLE
            return self.stream_function(5, 4)(result)

        if not set(alids) <= set(self.alarms.keys()):
            return self.stream_function(5, 4)(data_items.ACKC5.ERROR)

        for alid in alids:
            self.alarms[alid].enabled = s5f3_instance.ALED.get() == data_items.ALED.ENABLE
        return self.stream_function(5, 4)(result)

    def _on_s05f05(self, *args) -> functions.SecsS05F06:
        """接收到工厂下发的 S05F05, 查询报警信息, alid 空列表代表查询所有报警信息.

        Args:
            handler: handler the message was received on.
            message: complete message received.

        Returns:
            SecsS05F06: 返回 SecsS05F06 实例.
        """
        s5fs5_instance = self.get_sf_instance(args[-1])
        alids = s5fs5_instance.get()

        if isinstance(alids, int):
            alids = [alids]

        if not alids:
            alids = list(self.alarms.keys())

        result = [{
            "ALCD": self.alarms[alid].code | (data_items.ALCD.ALARM_SET if self.alarms[alid].set else 0),
            "ALID": alid,
            "ALTX": self.alarms[alid].text,
        } for alid in alids if alid in self.alarms]

        return self.stream_function(5, 6)(result)

    def _on_s07f01(self, *args) -> functions.SecsS07F02:
        """接收到下发的 S07F01, 询问是否可以下发配方.

        Args:
            handler: handler the message was received on.
            message: complete message received.

        Returns:
            SecsS07F02: 返回 SecsS07F02 实例.
        """
        data = self.get_receive_data_dict(args[1])
        recipe_name = data.get("PPID", "")
        recipe_length = data.get("LENGTH", 0)
        self.logger.info("收到的 PPID 是: %s, LENGTH 是 %s", recipe_name, recipe_length)
        if recipe_name in self.recipe_names:
            result = data_items.PPGNT.ALREADY_HAVE
        else:
            result = data_items.PPGNT.OK
        return self.stream_function(7, 2)(result)

    def _on_s07f03(self, *args) -> functions.SecsS07F04:
        """接收到下发配方信息, 保存配方字节数据到数据库.

        Args:
            handler: handler the message was received on.
            message: complete message received.

        Returns:
            SecsS07F04: 返回 SecsS07F04 实例.
        """
        self.__update_recipe_info(args[-1])
        return self.stream_function(7, 4)(data_items.ACKC7.ACCEPTED)

    def _on_s07f05(self, *args) -> functions.SecsS07F06:
        """接收到工厂请求上传配方信息.

        Args:
            handler: handler the message was received on.
            message: complete message received.

        Returns:
            SecsS07F06: 返回 SecsS07F06 实例.
        """
        recipe_name = self.get_receive_data_dict(args[-1])
        recipe_body = self.__get_recipe_info(args[-1])
        return self.stream_function(7, 6)({"PPID": recipe_name, "PPBODY": recipe_body})

    def _on_s07f17(self, *args) -> functions.SecsS07F18:
        """接收到删除配方请求.

        Args:
            handler: handler the message was received on.
            message: complete message received.

        Returns:
            SecsS07F18: 返回 SecsS07F18 实例.
        """
        recipe_name_list = self.get_receive_data_dict(args[1])
        if not recipe_name_list: # 删除所有配方信息
            self.mysql_secs.delete_data(models_class.RecipeInfo)
            return self.stream_function(7, 18)(data_items.ACKC7.ACCEPTED)

        if not set(recipe_name_list) <= set(self.recipe_names):
            return self.stream_function(7, 18)(data_items.ACKC7.PPID_NOT_FOUND)

        for recipe_name in recipe_name_list:
            recipe_filter = {"recipe_name": recipe_name}
            self.mysql_secs.delete_data(models_class.RecipeInfo, recipe_filter)

        return self.stream_function(7, 18)(data_items.ACKC7.ACCEPTED)

    def _on_s07f19(self, *args) -> functions.SecsS07F20:
        """查看设备的所有配方.

        Args:
            handler: handler the message was received on
            message: complete message received

        Returns:
            SecsS07F20: 返回 SecsS07F20 实例.
        """
        self.logger.info("收到的参数是: %s", args)
        return self.stream_function(7, 20)(self.recipe_names)

    def _on_s07f23(self, *args) -> functions.SecsS07F04:
        """接收到通过 S7F23 下发配方信息, 保存配方字节数据到数据库.

        Args:
            handler: handler the message was received on.
            message: complete message received.

        Returns:
            SecsS07F24: 返回 SecsS07F24 实例.
        """
        self.__update_recipe_info(args[-1])
        return self.stream_function(7, 24)(data_items.ACKC7.ACCEPTED)

    def _on_s07f25(self, *args) -> functions.SecsS07F06:
        """接收到 S7F25 工厂请求上传配方信息.

        Args:
            handler: handler the message was received on.
            message: complete message received.

        Returns:
            SecsS07F26: 返回 SecsS07F26 实例.
        """
        recipe_name = self.get_receive_data_dict(args[-1])
        recipe_body = self.__get_recipe_info(recipe_name)
        recipe_body_load = json.loads(recipe_body)
        if isinstance(recipe_body_load, dict):
            recipe_body_load = [
                {"CCODE": ccode, "PPARM": param if isinstance(param, list) else [param]}
                for ccode, param in recipe_body_load.items()
            ]

        s7f26_data = {
            "PPID": recipe_name, "MDLN": self.model_name, "SOFTREV": self.software_version,
            "CCODE": recipe_body_load,
        }
        return self.stream_function(7, 26)(s7f26_data)

    def _on_s10f03(self, *args) -> functions.SecsS10F04:
        """Eap 下发弹框信息.

        Args:
            *args: handler 和 message.

        Returns:
            SecsS10F04: 返回 SecsS10F04 实例.
        """
        display_data = self.get_receive_data_dict(args[1])
        terminal_id = display_data.get("TID", 0)
        terminal_text = display_data.get("TEXT", "")
        self.logger.info("接收到的弹框信息是, terminal_id: %s, terminal_text: %s", terminal_id, terminal_text)
        return self.stream_function(10, 4)(ACKC10.ACCEPTED)

    def _set_ce_state(self, ceed: bool, ceids: list[int | str]) -> bool:
        """En-/Disable event reports for the supplied ceids (or all, if ceid is an empty list).

        Args:
            ceed: Enable (True) or disable (False) event reports
            ceids: List of collection events

        Returns:
            True if all ceids were ok, False if illegal ceid was supplied
        """
        result = True
        if not ceids:
            for collection_event in self._registered_collection_events.values():
                collection_event.enabled = ceed
        else:
            for ceid in ceids:
                if ceid in self.collection_events:
                    if ceid in self._registered_collection_events:
                        self._registered_collection_events[ceid].enabled = ceed
                    else:
                        result = False
        return result

    async def operate_func_socket(self, byte_data: bytes) -> str:
        """收到客户端数据执行操作并返回数据.

        Args:
            byte_data: 收到的数据.

        Returns:
            str: 返回数据.
        """
        str_data = byte_data.decode("UTF-8")  # 解析接收的下位机数据
        receive_dict = json.loads(str_data)
        receive_key, receive_info = list(receive_dict.items())[0]
        reply_real = {receive_key: "OK"}
        self.logger.info("收到的下位机关键字是: %s", receive_key)
        self.logger.info("收到的下位机关键字对应的数据是: %s", receive_info)
        if call_func:= getattr(self, receive_key, None):
            if reply_data := await call_func(receive_info):
                reply_real = {receive_key: reply_data}

        self.logger.info("返回的数据是: %s", reply_real)
        return json.dumps(reply_real)

    def update_enabled_alarm(self, message: HsmsMessage):
        """增加或删除启用的报警.

        Args:
            message: HsmsMessage 消息数据实例.
        """
        data = self.get_receive_data_dict(message)
        is_enable = data["ALED"]
        alarm_ids = data.get("ALID")
        if isinstance(alarm_ids, int):
            alarm_ids = [alarm_ids]

        if not alarm_ids:
            self.mysql_secs.delete_data(models_class.AlarmEnabled)
            if is_enable == 128:
                add_enabled_alarm_list = [{"alarm_id": alarm_id} for alarm_id in self.alarms.keys()]
                self.mysql_secs.add_data(models_class.AlarmEnabled, add_enabled_alarm_list)
            return

        for alarm_id in alarm_ids:
            if is_enable == 128:
                if not self.mysql_secs.query_data(models_class.AlarmEnabled, {"alarm_id": alarm_id}):
                    self.mysql_secs.add_data(models_class.AlarmEnabled, [{"alarm_id": alarm_id}])
            else:
                self.mysql_secs.delete_data(models_class.AlarmEnabled, {"alarm_id": alarm_id})

    def update_define_report(self, message: HsmsMessage):
        """增加或删除定义的报告.

        Args:
            message: HsmsMessage 消息数据实例.
        """
        data_list = self.get_receive_data_dict(message)["DATA"]
        if data_list:
            add_data = []
            for report_link_vid_dict in data_list:
                report_id = report_link_vid_dict["RPTID"]
                vid_list = report_link_vid_dict["VID"]
                if vid_list:
                    add_data.append({"report_id": report_id, "variable_ids": ",".join([str(_) for _ in vid_list])})
                else:
                    # 获取所有的定义事件关联报告
                    event_list = self.mysql_secs.query_data(models_class.ReportLinkEvent)
                    for event_info_dict in event_list:
                        report_str_list = event_info_dict["report_ids"].split(",")
                        report_str_list_copy = copy.deepcopy(report_str_list)
                        if str(report_id) in report_str_list and len(report_str_list) != 1: # 判断要删除的报告是否关联了此事件
                            report_str_list_copy.remove(str(report_id))
                            event_filter = {"event_id": event_info_dict["event_id"]}
                            update_dict = {"report_ids": ",".join(report_str_list_copy)}
                            self.mysql_secs.update_data(models_class.ReportLinkEvent, update_dict, event_filter)
                self.mysql_secs.delete_data(models_class.DefineReport, {"report_id": report_id})
                self.mysql_secs.delete_data(models_class.ReportLinkEvent, {"report_ids": str(report_id)})
            self.mysql_secs.add_data(models_class.DefineReport, add_data)
        else:
            self.mysql_secs.delete_data(models_class.DefineReport)
            self.mysql_secs.delete_data(models_class.ReportLinkEvent)

    def update_register_event_report(self, message: HsmsMessage):
        """增加或删除注册的事件和报告.

        Args:
            message: HsmsMessage 消息数据实例.
        """
        data_list = self.get_receive_data_dict(message)["DATA"]
        if data_list:
            add_data = []
            for report_link_event_dict in data_list:
                event_id = report_link_event_dict["CEID"]
                report_list = report_link_event_dict["RPTID"]
                event_id_filter = {"event_id": event_id}
                if report_list and event_id in self.collection_events:  # 此事件新增关联的报告不是空
                    add_data.append({"event_id": event_id, "report_ids": ",".join([str(_) for _ in report_list])})
                    self.mysql_secs.delete_data(models_class.ReportLinkEvent, event_id_filter)
                else:
                    # 删除此事件关联的所有报告
                    self.mysql_secs.delete_data(models_class.ReportLinkEvent, event_id_filter)
            self.mysql_secs.add_data(models_class.ReportLinkEvent, add_data)
        else:
            # 删除所有定义的事件关联报告
            self.mysql_secs.delete_data(models_class.ReportLinkEvent)

    def update_register_event_enable_disable(self, message: HsmsMessage):
        """注册的事件禁用或启用.

        Args:
            message: HsmsMessage 消息数据实例.
        """
        data_dict = self.get_receive_data_dict(message)
        ceed = data_dict["CEED"]
        event_id_list = data_dict["CEID"]
        update_data = {"state": ceed}
        if event_id_list:
            for event_id in event_id_list:
                self.mysql_secs.update_data(models_class.ReportLinkEvent, update_data, {"event_id": event_id})
        else:
            # 将全部已经注册的事件启用或停用
            self.mysql_secs.update_data(models_class.ReportLinkEvent, update_data)

    def s02f33_pre(self, message: HsmsMessage) -> tuple[bool, int]:
        """接收到 S2F33 进行预检查, 检查通过保存注册的报告.

        Args:
            message: HsmsMessage 消息数据实例.

        Returns:
            tuple[bool, int]: 返回检查结果.
        """
        if self.is_host:  # 是 host 进行是否所有设备都连接了检查, 同时给设备发送消息
            return getattr(self, "send_sf_pre_check")(message, self.update_define_report)

        self.update_define_report(message)
        return True, 0

    def s02f35_pre(self, message: HsmsMessage) -> tuple[bool, int]:
        """接收到 S2F35 进行预检查, 检查通过保存注册的事件, 同时保存事件关联报告.

        Args:
            message: HsmsMessage 消息数据实例.

        Returns:
            tuple[bool, int]: 返回检查结果.
        """
        if self.is_host:  # 是 host 进行是否所有设备都连接了检查, 同时给设备发送消息
            return getattr(self, "send_sf_pre_check")(message, self.update_register_event_report)

        self.update_register_event_report(message)
        return True, 0

    def s02f37_pre(self, message: HsmsMessage) -> tuple[bool, int]:
        """接收到 S2F37 进行预检查, 检查通过保存事件状态.

        Args:
            message: HsmsMessage 消息数据实例.

        Returns:
            tuple[bool, int]: 返回检查结果.
        """
        if self.is_host:  # 是 host 进行是否所有设备都连接了检查, 同时给设备发送消息
            return getattr(self, "send_sf_pre_check")(message, self.update_register_event_enable_disable)

        data_dict = self.get_receive_data_dict(message)
        if not data_dict["CEED"] and not data_dict["CEID"]:  # 删除所有的注册事件
            self.mysql_secs.delete_data(models_class.ReportLinkEvent)
        self.update_register_event_enable_disable(message)
        return True, 0

    def s05f03_pre(self, message: HsmsMessage) -> tuple[bool, int]:
        """接收到 S5F5 进行预检查, 检查通过保存启用的报警.

        Args:
            message: HsmsMessage 消息数据实例.

        Returns:
            tuple[bool, int]: 返回检查结果.
        """
        if self.is_host:  # 是 host 进行是否所有设备都连接了检查, 同时给设备发送消息
            return getattr(self, "send_sf_pre_check")(message, self.update_enabled_alarm)

        self.update_enabled_alarm(message)
        return True, 0

    def on_dv_value_request(self, dv_id: variables.U4, data_value: DataValue) -> variables.Base:
        """获取 secs 格式的 dv 值.

        Args:
            dv_id: dv id.
            data_value: dv 实例.

        Returns:
            variables.Base: 返回 secs 正确 secs 个格式的 dv 值.
        """
        if issubclass(data_value.value_type, variables.Array):
            # noinspection PyUnresolvedReferences
            base_value_type = data_value.base_value_type
            return variables.Array(base_value_type, data_value.value)
        return data_value.value_type(data_value.value)

    def decode_message(self, message: HsmsMessage) -> SecsStreamFunction:
        """解析 HsmsMessage 数据, 返回流函数实例.

        Args:
            message:

        Returns:
            SecsStreamFunction: 返回 SecsStreamFunction 实例.
        """
        return self.settings.streams_functions.decode(message)
