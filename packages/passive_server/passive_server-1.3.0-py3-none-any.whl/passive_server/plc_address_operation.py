# pylint: skip-file
from operator import itemgetter
from typing import Any, Optional

from mysql_api.mysql_database import MySQLDatabase

from passive_server import models_class
from passive_server.secs_config import get_ec_info


def get_address_with_description(mysql: MySQLDatabase, description: str) -> Optional[dict[str, Any]]:
    """根据地址描述获取 plc 地址信息.

    Args:
        mysql: 数据库实例.
        description: 根据描述信息获取地址信息.

    Returns:
       Optional[dict[str, Any]]: 返回 获取 plc 地址信息.
    """
    address_info_list = mysql.query_data(models_class.AddressList, {"description": description})
    if address_info_list:
        plc_type = mysql.query_data(models_class.EcList, {"ec_name": "plc_type"})[0]["value"]
        address_info = address_info_list[0]
        return get_address_info(plc_type, address_info)
    return None


def get_signal_address_list(mysql: MySQLDatabase) -> list[dict]:
    """获取所有的信号地址.

    Args:
        mysql: 数据库实例.

    Returns:
        list[dict]: 返回所有的信号地址.
    """
    address_info_list = mysql.query_data(models_class.SignalAddressList)
    return address_info_list


def get_current_signal_value(mysql: MySQLDatabase, signal_description: str) -> int:
    """获取当前信号值.

    Args:
        mysql: 数据库实例.
        signal_description: 信号描述.

    Returns:
        int: 当前信号值.
    """
    address_info_list = mysql.query_data(models_class.SignalAddressList, {"description": signal_description})
    return address_info_list[0]["current_signal_value"]


def get_signal_address_info(mysql: MySQLDatabase, plc_type: str, address: str) -> Optional[dict[str, Any]]:
    """获取信号地址信息.

    Args:
        mysql: 数据库实例.
        plc_type: plc 类型.
        address: 地址.

    Returns:
        Optional[dict[str, Any]]: 返回信号地址信息.
    """
    address_info_list = mysql.query_data(models_class.SignalAddressList, {"address": address})
    if address_info_list:
        address_info = address_info_list[0]
        return get_address_info(plc_type, address_info)
    return None


def get_signal_callbacks(mysql: MySQLDatabase, address: str) -> list:
    """获取信号的流程信息.

    Args:
        mysql: 数据库实例.
        address: 信号地址.

    Returns:
        list: 返回排序后的 call back 列表.
    """
    models_class_flow_func = models_class.FlowFunc
    filter_dict = {"associate_signal": address}
    callbacks_plc = mysql.query_data(models_class.PlcAddressList, filter_dict)
    callbacks_mes = mysql.query_data(models_class.MesAddressList, filter_dict)
    callbacks_flow_func = mysql.query_data(models_class_flow_func, filter_dict)
    callbacks = callbacks_plc + callbacks_mes + callbacks_flow_func
    callbacks_return = sorted(callbacks, key=itemgetter("step"))
    return callbacks_return


def get_address_info(plc_type: str, address_info: dict, mysql: MySQLDatabase = None) -> dict[str, Any]:
    """根据数据库查询的地址信息获取整理后的地址信息.

    Args:
        plc_type: plc 类型.
        address_info: 数据库获取的地址信息
        mysql: 数据库实例, 默认 None.

    Returns:
        dict[str, Any]: 整理后的地址信息.
    """
    if "tag" in plc_type:
        address_info_expect = {"address": address_info["address"], "data_type": address_info["data_type"]}
    elif "snap7" in plc_type:
        db_num = get_ec_info(mysql, {"ec_name": "db_num"})["value"]
        address_info_expect = {
            "address": address_info["address"], "data_type": address_info["data_type"],
            "size": address_info.get("size", 2), "db_num": db_num,
            "bit_index": address_info.get("bit_index", 0)
        }
    elif "mitsubishi" in plc_type:
        address_info_expect = {
            "address": address_info["address"], "data_type": address_info["data_type"],
            "size": address_info["size"]
        }
    elif "modbus" in plc_type:
        address_info_expect = {
            "address": address_info["address"], "data_type": address_info["data_type"],
            "size": address_info.get("size", 1), "bit_index": address_info.get("bit_index", 0)
        }
    else:
        address_info_expect = {}
    return address_info_expect
