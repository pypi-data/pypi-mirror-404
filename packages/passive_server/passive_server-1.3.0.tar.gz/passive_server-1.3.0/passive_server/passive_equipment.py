# pylint: skip-file
"""这个类是设备端 secs passive 服务的实现, 继承了 PassiveServer 类."""
import json
import threading
import time

from typing import Union, Any, Optional

from secsgem.secs import variables
from socket_cyg.socket_server_asyncio import CygSocketServerAsyncio
from passive_server import secs_config, factory, plc_address_operation, passive_server, models_class


class EquipmentPassive(passive_server.PassiveServer):
    """EquipmentPassive class."""

    def __init__(self, mysql_host: str, database_name: str, user_name: str = "root"):
        """EquipmentPassive 构造函数.

        Args:
            mysql_host: 配置数据所在的数据库 ip 地址.
            database_name: 所在数据库名称.
            user_name: 数据库用户名.
        """

        super().__init__(mysql_host, database_name, user_name)
        self.plc_type = secs_config.get_plc_type(self.mysql_secs)
        self.plc = factory.get_plc_instance(self.mysql_secs, self.plc_type)
        self.plc.logger.addHandler(self.file_handler)
        self.mysql = factory.get_mysql_instance(
            self.get_ec_value_with_name("mysql_host"),
            self.get_ec_value_with_name("mysql_database"),
            self.get_ec_value_with_name("mysql_user_name")
        )
        self._monitor_plc_thread()

    @property
    def open_plc(self) -> bool:
        """是否打开和 plc 的连接.

        Returns:
            bool: True 打开和 plc 的连接, False 不打开和 plc 的连接.
        """
        return self.get_ec_value_with_name("is_monitor_plc", False)

    def __start_monitor_plc_thread(self):
        """启动监控 plc 的线程."""
        threading.Thread(target=self._mes_heart, daemon=True).start()
        threading.Thread(target=self._control_state_local, daemon=True).start()
        threading.Thread(target=self._process_state, daemon=True).start()
        threading.Thread(target=self._current_recipe, daemon=True).start()
        for signal_address_info in plc_address_operation.get_signal_address_list(self.mysql_secs):
            if signal_address_info.get("state", False):  # 实时监控的信号才会创建线程
                threading.Thread(
                    target=self._monitor_plc_address, daemon=True,
                    args=(signal_address_info,),
                ).start()

    def _monitor_plc_thread(self):
        """监控 plc 的线程."""
        if self.get_ec_value_with_name("is_monitor_plc"):
            self.logger.info("真实监控plc.")
            if self.plc.communication_open():
                self.logger.info("首次连接 plc 成功, ip: %s", self.plc.ip)
            else:
                self.logger.warning("首次连接 %s plc 失败", self.plc.ip)
            self.__start_monitor_plc_thread()
        else:
            self.logger.info("不监控plc.")

    def _mes_heart(self):
        """Mes 心跳."""
        address_info = plc_address_operation.get_address_with_description(self.mysql_secs, "MES 心跳")
        if "snap7" in self.plc_type:
            address_info.update({"db_num": self.get_ec_value_with_name("db_num")})
        mes_heart_gap = self.get_ec_value_with_name("mes_heart_gap")
        while True:
            try:
                self.plc.execute_write(**address_info, value=True, save_log=False)
                time.sleep(mes_heart_gap)
                self.plc.execute_write(**address_info, value=False, save_log=False)
                time.sleep(mes_heart_gap)
            except Exception as e:
                if self.get_sv_value_with_name("ControlState") != 3:
                    self.set_sv_value_with_name("ControlState", 3)
                    self.send_s6f11("ControlStateChange")
                    self.send_s6f11("EquipmentOffline")
                self.logger.warning("写入心跳失败, 错误信息: %s", str(e))
                self.plc = factory.get_plc_instance(self.mysql_secs, self.plc_type)
                if self.plc.communication_open():
                    self.logger.info("Plc重新连接成功.")
                else:
                    self.logger.warning("Plc重新连接失败, 等待 5 秒后尝试重新连接.")
                time.sleep(5)

    def _control_state_local(self):
        """监控设备是本地模式还是远程在线模式."""
        address_info = plc_address_operation.get_address_with_description(self.mysql_secs, "本地模式 | 远程模式")
        while True:
            try:
                time.sleep(1)
                control_state = self.plc.execute_read(**address_info, save_log=False)
                control_state_real = 7 if control_state else 8
                if control_state_real != self.get_sv_value_with_name("ControlState", save_log=False):
                    self.set_sv_value_with_name("ControlState", control_state_real, True)
                    self.send_s6f11("ControlStateChange")
                    if control_state_real == 7:
                        self.send_s6f11("ControlStateOnlineLocal")
                    else:
                        self.send_s6f11("ControlStateOnlineRemote")
            except RuntimeError as e:
                time.sleep(10)
                self.logger.warning("control_state_local 线程出现异常: %s.", str(e))

    def _process_state(self):
        """监控运行状态变化."""
        address_info = plc_address_operation.get_address_with_description(self.mysql_secs, "设备运行状态")
        occur_alarm_code = self.get_ec_value_with_name("occur_alarm_code")
        clear_alarm_code = self.get_ec_value_with_name("clean_alarm_code")
        alarm_state = self.get_ec_value_with_name("alarm_state")
        while True:
            try:
                time.sleep(1)
                process_state = self.plc.execute_read(**address_info, save_log=False)
                pre_process_state = self.get_sv_value_with_name("process_state", save_log=False)
                if process_state != pre_process_state:
                    if process_state == alarm_state:
                        self.set_clear_alarm_plc(occur_alarm_code)
                    elif self.get_sv_value_with_name("process_state") == alarm_state:
                        self.set_clear_alarm_plc(clear_alarm_code)
                    self.set_sv_value_with_name("previous_process_state", pre_process_state, True)
                    self.set_sv_value_with_name("process_state", process_state, True)
                    self.send_s6f11("ProcessStateChange")
            except RuntimeError as e:
                time.sleep(10)
                self.logger.warning("process_state 线程出现异常: %s.", str(e))

    def _current_recipe(self):
        """监控设备的当前配方 id."""
        address_info = plc_address_operation.get_address_with_description(self.mysql_secs, "当前配方")
        data_type = address_info["data_type"]
        if data_type == "string":
            recipe_sv_name = "recipe_name"
        else:
            recipe_sv_name = "recipe_id"
        while True:
            try:
                time.sleep(2)
                current_recipe = self.plc.execute_read(**address_info, save_log=False)
                if current_recipe != self.get_sv_value_with_name(recipe_sv_name, save_log=False):
                    self.set_sv_value_with_name(recipe_sv_name, current_recipe)
                    if recipe_sv_name == "recipe_id":
                        current_recipe_name = secs_config.get_recipe_name_with_id(self.mysql_secs, current_recipe)
                        self.set_sv_value_with_name("recipe_name", current_recipe_name)
            except RuntimeError as e:
                time.sleep(10)
                self.logger.warning("recipe_id 线程出现异常: %s.", str(e))

    def _monitor_plc_address(self, address_info: dict[str, Any]):
        """监控 plc 信号.

        Args:
            address_info: 地址.
        """
        address_info_read = plc_address_operation.get_signal_address_info(
            self.mysql_secs, self.plc_type, address_info["address"]
        )
        callbacks = plc_address_operation.get_signal_callbacks(self.mysql_secs, address_info["address"])
        signal_value = address_info["signal_value"]
        clean_signal_value = address_info["clean_signal_value"]
        description = address_info["description"]
        _ = "=" * 40
        while True:
            try:
                current_value = self.plc.execute_read(**address_info_read, save_log=False)
                if current_value == signal_value:
                    self.logger.info("%s 监控到 %s 信号 %s", _, description, _)
                    self.get_signal_to_execute_callbacks(callbacks)
                    final_step_num = len(callbacks) + 1
                    self.logger.info("%s 第 %s 步: 清除%s %s", "-" * 30, final_step_num, description, "-" * 30)
                    self.write_clean_signal_value(address_info, clean_signal_value)
                    self.logger.info("%s 清除%s 结束 %s", "-" * 30, description, "-" * 30)
                    self.logger.info("%s 执行 %s 结束 %s", _, description, _)
                time.sleep(1)
            except RuntimeError:
                time.sleep(10)

    def _is_send_event(self, event_id: Optional[int]):
        """判断是否要发送事件.

        Arg:
            event_id: 要发送的事件 id, 默认 None.
        """
        if event_id:
            self.send_s6f11(event_id)

    def set_clear_alarm_plc(self, alarm_code: int):
        """通过S5F1发送报警和解除报警.

        Args:
            alarm_code: 报警 code, 128: 报警, 0: 清除报警.
        """
        address_info = plc_address_operation.get_address_with_description(self.mysql_secs, "出现报警时的报警代码")
        alarm_id = self.plc.execute_read(**address_info, save_log=False)
        self.set_clear_alarm(alarm_code, alarm_id)

    def set_clear_alarm(self, alarm_code: int, alarm_id: int):
        """设备报警或清除报警.

        Args:
            alarm_code: 报警 code, 128: 出现报警, 0: 消除报警.
            alarm_id: 报警 id.
        """
        try:
            alarm_id = int(alarm_id)
        except ValueError:
            alarm_id = 0
            self.logger.warning("报警 id 非法, 报警id: %s", alarm_id)

        if alarm_id in self.alarms:
            alarm_text_en = self.alarms[alarm_id].text
            # noinspection PyUnresolvedReferences
            alarm_text_zh = self.alarms[alarm_id].text_zh
        else:
            alarm_text_en = "alarm not define"
            alarm_text_zh = "报警未在报警列表定义"

        if alarm_code == 128:
            self.save_alarm(alarm_id, alarm_text_zh)
            self.logger.info("出现报警, %s %s", alarm_id, alarm_text_zh)
        else:
            self.logger.info("清除报警, %s %s", alarm_id, alarm_text_zh)

        if alarm_id in self.alarms and self.alarms[alarm_id].enabled:
            self.send_alarm(alarm_code, alarm_id, alarm_text_en)

    def alarm_sender(self, alarm_code: int, alarm_id: variables.U4, alarm_text: str):
        """发送报警和解除报警.

        Args:
            alarm_code: 报警代码.
            alarm_id: 报警 id.
            alarm_text: 报警内容.
        """
        self.send_and_waitfor_response(
            self.stream_function(5, 1)({"ALCD": alarm_code, "ALID": alarm_id, "ALTX": alarm_text})
        )

    def send_alarm(self, alarm_code: int, alarm_id: int, alarm_text: str):
        """发送并保存报警信息.

        Args:
            alarm_code: alarm_code.
            alarm_id: 报警 id.
            alarm_text: 报警内容.
        """
        threading.Thread(
            target=self.alarm_sender, args=(alarm_code, variables.U4(alarm_id), alarm_text,), daemon=True
        ).start()

    def save_alarm(self, alarm_id: int, alarm_text: str):
        """保存报警.

        Args:
            alarm_id: 报警 id.
            alarm_text: 中文报警内容.
        """
        alarm_info = {"alarm_id": alarm_id, "alarm_text": alarm_text}
        self.mysql_secs.add_data(models_class.AlarmRecordList, [alarm_info])

    def get_signal_to_execute_callbacks(self, callbacks: list):
        """监控到信号执行 call_backs.

        Args:
            callbacks: 要执行的流程信息列表.
        """
        for i, callback in enumerate(callbacks, 1):
            description = callback.get("description")
            self.logger.info("%s 第 %s 步: %s %s", "-" * 30, i, description, "-" * 30)

            operation_type = callback.get("operation_type")
            if operation_type == "read":
                self.read_update_sv_or_dv(callback)

            if operation_type == "write":
                self.write_sv_or_dv_value(callback)

            if func_name := callback.get(f"func_name"):
                getattr(self, func_name)(callback)

            self._is_send_event(callback.get("event_id"))
            self.logger.info("%s %s 结束 %s", "-" * 30, description, "-" * 30)

    def read_update_sv_or_dv(self, callback: dict):
        """读取 plc 数据更新 sv 值.

        Args:
            callback: 要执行的 callback 信息.
        """
        sv_or_dv_id = int(callback.get("associate_sv_or_dv"))
        count_num = callback.get("count_num", 1)
        address_info = plc_address_operation.get_address_info(self.plc_type, callback)
        if count_num == 1:
            plc_value = self.plc.execute_read(**address_info)
        else:
            read_multiple_value_func = getattr(self, f"read_multiple_value_{self.plc_type}")
            plc_value = read_multiple_value_func(callback)
        self.set_sv_or_dv_value_with_id(sv_or_dv_id, plc_value)

    def read_multiple_value_snap7(self, callback: dict) -> list:
        """读取 Snap7 plc 多个数据.

        Args:
            callback: callback 信息.

        """
        value_list = []
        count_num = callback["count_num"]
        gap = callback.get("gap", 1)
        start_address = int(callback.get("address"))
        for i in range(count_num):
            real_address = start_address + i * gap
            address_info = {
                "address": real_address,
                "data_type": callback.get("data_type"),
                "db_num": self.get_ec_value_with_name("db_num"),
                "size": callback.get("size", 1),
                "bit_index": callback.get("bit_index", 0)
            }
            plc_value = self.plc.execute_read(**address_info)
            value_list.append(plc_value)
            self.logger.info("读取 %s 的值是: %s", real_address, plc_value)
        return value_list

    def read_multiple_value_tag(self, callback: dict) -> list:
        """读取标签通讯 plc 多个数据值.

        Args:
            callback: callback 信息.
        """
        value_list = []
        for i in range(1, callback["count_num"] + 1):
            real_address = callback["address"].replace("$", str(i))
            address_info = {"address": real_address, "data_type": callback["data_type"]}
            plc_value = self.plc.execute_read(**address_info)
            value_list.append(plc_value)
            self.logger.info("读取 %s 的值是: %s", real_address, plc_value)
        return value_list

    def read_multiple_value_modbus(self, callback: dict) -> list:
        """读取 modbus 通讯 plc 多个数据值.

        Args:
            callback: callback 信息.
        """
        value_list = []
        count_num = callback["count_num"]
        start_address = int(callback.get("address"))
        size = callback.get("size")
        for i in range(count_num):
            real_address = start_address + i * size
            address_info = {
                "address": real_address,
                "data_type": callback.get("data_type"),
                "size": size
            }
            plc_value = self.plc.execute_read(**address_info)
            value_list.append(plc_value)
            self.logger.info("读取 %s 的值是: %s", real_address, plc_value)
        return value_list

    def write_sv_or_dv_value(self, callback: dict):
        """向 plc 地址写入 sv 或 dv 值.

        Args:
            callback: 要执行的 callback 信息.
        """
        sv_or_dv_id = int(callback.get("associate_sv_or_dv"))
        value = self.get_sv_or_dv_value_with_id(sv_or_dv_id)
        count_num = callback.get("count_num", 1)
        address_info = plc_address_operation.get_address_info(self.plc_type, callback)
        if count_num == 1:
            self.plc.execute_write(**address_info, value=value)
        else:
            write_multiple_value_func = getattr(self, f"write_multiple_value_{self.plc_type}")
            write_multiple_value_func(callback, value)

        if "snap7" in self.plc_type and address_info.get("data_type") == "bool":
            self.confirm_write_success(address_info, value)  # 确保写入成功

    def write_multiple_value_snap7(self, callback: dict, value_list: list):
        """向 snap7 plc 地址写入多个值.

        Args:
            callback: callback 信息.
            value_list: 写入的值列表.
        """
        gap = callback.get("gap", 1)
        for i, value in enumerate(value_list):
            address_info = {
                "address": int(callback.get("address")) + gap * i,
                "data_type": callback.get("data_type"),
                "db_num": self.get_ec_value_with_name("db_num"),
                "size": callback.get("size", 2),
                "bit_index": callback.get("bit_index", 0)
            }
            self.plc.execute_write(**address_info, value=value)

    def write_multiple_value_tag(self, callback: dict, value_list: list):
        """向汇川 plc 标签通讯地址写入多个值.

        Args:
            callback: callback 信息.
            value_list: 写入的值列表.
        """
        for i, value in enumerate(value_list, 1):
            address_info = {
                "address": callback.get("address").replace("$", str(i)),
                "data_type": callback.get("data_type"),
            }
            self.plc.execute_write(**address_info, value=value)

    def write_multiple_value_modbus(self, callback: dict, value_list: list):
        """向 modbus 通讯地址写入多个值.

        Args:
            callback: callback 信息.
            value_list: 写入的值列表.
        """
        start_address = callback.get("address")
        size = callback.get("size")
        for i, value in enumerate(value_list, 0):
            address_info = {
                "address": int(start_address) + i * size,
                "data_type": callback.get("data_type"),
            }
            self.plc.execute_write(**address_info, value=value)

    def write_clean_signal_value(self, address_info: dict, value: int):
        """向 plc 地址写入清除信号值.

        Args:
            address_info: 要写入的地址信息.
            value: 要写入的值.
        """
        address_info_write = plc_address_operation.get_address_info(self.plc_type, address_info)
        self.confirm_write_success(address_info_write, value)

    def confirm_write_success(self, address_info: dict, value: Union[int, float, bool, str]):
        """向 plc 写入数据, 并且一定会写成功.

        在通过 S7 协议向西门子 plc 写入数据的时候, 会出现写不成功的情况, 所以再向西门子plc写入时调用此函数.
        为了确保数据写入成功, 向任何 plc 写入数据都可调用此函数, 但是交互的时候每次会多读一次 plc.

        Args:
            address_info: 写入数据的地址位信息.
            value: 要写入的数据.
        """
        self.plc.execute_write(**address_info, value=value)
        while self.plc.execute_read(**address_info) != value:
            self.logger.warning(f"向地址 %s 写入 %s 失败", address_info.get("address"), value)
            self.plc.execute_write(**address_info, value=value)

    def execute_pp_select(self, recipe_name: str):
        """执行切换配方操作.

        Args:
            recipe_name: 要切换的配方名称.
        """
        self.set_sv_value_with_name("pp_select_recipe_name", recipe_name)
        pp_select_recipe_id = secs_config.get_recipe_id_with_name(self.mysql_secs, recipe_name)
        self.set_sv_value_with_name("pp_select_recipe_id", pp_select_recipe_id)

        if recipe_name != self.get_sv_value_with_name("recipe_name"):
            self.execute_callbacks_of_signal("pp_select")
            current_recipe_id = self.get_sv_value_with_name("recipe_id")
            current_recipe_name = secs_config.get_recipe_name_with_id(self.mysql_secs, current_recipe_id)
            self.set_sv_value_with_name("recipe_name", current_recipe_name)
            if current_recipe_id == pp_select_recipe_id:
                pp_select_state = 1
            else:
                pp_select_state = 2
        else:
            pp_select_state = 1

        self.set_sv_value_with_name("pp_select_state", pp_select_state)
        self.send_s6f11("pp_select_result")

    def execute_new_lot(self, lot_name: str, lot_quantity: int):
        """执行开工单.

        Args:
            lot_name: 工单名称.
            lot_quantity: 工单数量.
        """
        lot_quantity = int(lot_quantity)
        self.set_sv_value_with_name("lot_name", lot_name)
        self.set_sv_value_with_name("lot_quantity", lot_quantity)
        self.execute_callbacks_of_signal("new_lot")

    def execute_end_lot(self):
        """执行结束工单."""
        self.execute_callbacks_of_signal("end_lot")

    def execute_callbacks_of_signal(self, signal_address: str):
        """执行信号关联的步骤.

        Args:
            signal_address: 信号地址.
        """
        address_info = plc_address_operation.get_signal_address_info(self.mysql_secs, self.plc_type, signal_address)
        callbacks = plc_address_operation.get_signal_callbacks(self.mysql_secs, address_info["address"])
        self.get_signal_to_execute_callbacks(callbacks)

    def new_lot_pre_check(self):
        """开工单前检查上个工单是否做完."""
        do_quantity = self.get_sv_value_with_name("do_quantity")
        lot_quantity = self.get_sv_value_with_name("lot_quantity")
        if do_quantity < lot_quantity and do_quantity != 0:
            return False
        return True

    def wait_host_reply(self, callback: dict):
        """等待工厂反馈.

        Args:
            callback: 要执行的 callback 信息.
        """
        wait_time = 0
        dv_id = int(callback.get("associate_dv"))
        is_wait = callback.get("is_wait")
        wait_eap_reply_time = self.get_ec_value_with_name("wait_time_eap_reply")
        reply_dv_name = f"{self.get_dv_name_with_id(dv_id)}_reply"
        while not self.get_dv_value_with_name(reply_dv_name):
            if is_wait:
                self.logger.info("需要等待工厂回复, 等待超时时间是: %s", wait_eap_reply_time)
                if wait_time >= wait_eap_reply_time:
                    self.set_dv_value_with_id(dv_id, 2)
                    break
            else:
                self.logger.info("不需要等待工厂回复, 默认可做")
                self.set_dv_value_with_id(dv_id, 1)
                self.set_dv_value_with_name(reply_dv_name, True)
                break

            time.sleep(0.5)
            wait_time += 0.5
            self.logger.info("工厂未反馈 %s, 已等待 %s 秒", callback["description"], round(wait_time, 1))

        self.set_dv_value_with_name(reply_dv_name, False)

    def clean_reply_flag(self, callback: dict):
        """清楚等待工厂回复标识.

        Args:
            callback:要执行的 callback 信息.
        """
        dv_id = int(callback.get("associate_dv"))
        self.set_dv_value_with_id(dv_id, False)

    def wait_time(self, callback: dict):
        """等待时间.

        Args:
            callback: callback 信息.
        """
        count_time = 0
        wait_time = self.get_dv_value_with_id(int(callback["associate_dv"]))
        while True:
            time.sleep(1)
            count_time += 1
            self.logger.info("等待 %s 秒", count_time)
            wait_time -= 1
            if wait_time == 0:
                break

    async def new_lot(self, lot_info: dict):
        """本地开工单.

        Args:
            lot_info: 工单信息.
        """
        lot_name, lot_quantity = lot_info["lot_name"], lot_info["lot_quantity"]
        lot_name = lot_info["lot_name"]
        if self.open_plc:
            self.execute_new_lot(lot_name, lot_quantity)
        data = {"new_lot": {"lot_name": lot_name, "lot_quantity": lot_quantity}}
        return await self.send_data_to_socket_client(
            self.socket_server_low, self.get_ec_value_with_name("socket_ip"), json.dumps(data)
        )

    async def end_lot(self, lot_name: str):
        """本地结束工单.

        Args:
            lot_name: 工单号.
        """
        data = {"end_lot": lot_name}
        self.set_sv_value_with_name("do_quantity", 0)
        if self.open_plc:
            self.execute_end_lot()
        self.send_s6f11("end_lot")
        return await self.send_data_to_socket_client(
            self.socket_server_low, self.get_ec_value_with_name("socket_ip"), json.dumps(data)
        )

    async def send_event(self, event_id: int):
        """发送事件.

        Args:
            event_id: 事件 id.
        """
        self.send_s6f11(event_id)

    async def send_data_to_socket_client(self, socket_instance: CygSocketServerAsyncio, client_ip: str, data: str) -> bool:
        """发送数据给 socket 下位机.

        Args:
            socket_instance: CygSocketServerAsyncio 实例.
            client_ip: 接收数据的设备ip地址.
            data: 要发送的数据.

        Return:
            bool: 是否发送成功.
        """
        status = True
        client_connection = socket_instance.clients.get(client_ip)
        if client_connection:
            byte_data = str(data).encode("UTF-8")
            await socket_instance.socket_send(client_connection, byte_data)
        else:
            self.logger.warning("发送失败: %s 未连接", client_ip)
            status = False
        return status
