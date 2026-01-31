# pylint: skip-file
from typing import Any, Optional

from mysql_api.mysql_database import MySQLDatabase
from secsgem import gem

from passive_server import models_class, common_func
from passive_server.enum_sece_data_type import EnumSecsDataType


def get_report_link_info(mysql: MySQLDatabase) -> list:
    """获取报告关联的 sv 和 dv.

    Args:
        mysql: 数据库实例对象.

    Returns:
        list: 报告关联的变量列表.
    """
    report_link_list = []
    report_info_list = mysql.query_data(models_class.ReportList)
    for report_info in report_info_list:
        link_sv_dvs = [int(sv_id) for sv_id in report_info["associate_sv_dv"].split(",") if sv_id]
        report_link_list.append({int(report_info["report_id"]): link_sv_dvs})
    return report_link_list


def get_sv_list(mysql: MySQLDatabase) -> list[dict[int, gem.StatusVariable]]:
    """获取所有的 sv.

    Args:
        mysql: 数据库实例对象.

    Returns:
        list[dict[int, gem.StatusVariable]]: 返回 sv 列表.
    """
    sv_list = mysql.query_data(models_class.SvList)
    sv_list_return = []
    for sv in sv_list:
        sv_id = sv["sv_id"]
        sv_dict = {
            "svid": sv_id, "name": sv["sv_name"], "unit": "",
            "value_type": getattr(EnumSecsDataType, sv["value_type"]).value,
            "value": common_func.parse_value(sv["value"], sv["value_type"])
        }
        sv_list_return.append({sv_id: gem.StatusVariable(**sv_dict)})
    return sv_list_return


def get_dv_info(mysql: MySQLDatabase, filter_dict: dict) -> Optional[dict[str, Any]]:
    """根据条件获取 dv 信息.

    Args:
        mysql: 数据库实例对象.
        filter_dict: 条件.

    Returns:
        Optional[dict[str, Any]]: 返回 dv 信息, 查询不到返回 None.
    """
    dv_list = mysql.query_data(models_class.DvList, filter_dict)
    if dv_list:
        return dv_list[0]
    return None


def get_ec_info(mysql: MySQLDatabase, filter_dict: dict) -> Optional[dict[str, Any]]:
    """根据条件获取 ec 信息.

    Args:
        mysql: 数据库实例对象.
        filter_dict: 条件.

    Returns:
        Optional[dict[str, Any]]: 返回 ec 信息, 查询不到返回 None.
    """
    ec_list = mysql.query_data(models_class.EcList, filter_dict)
    if ec_list:
        return ec_list[0]
    return None


def get_dv_list(mysql: MySQLDatabase) -> list[dict[int, gem.DataValue]]:
    """获取所有的 dv.

    Args:
        mysql: 数据库实例对象.

    Returns:
        list[dict[int, gem.DataValue]]: 返回 dv 列表.
    """
    dv_list = mysql.query_data(models_class.DvList)
    dv_list_return = []
    for dv in dv_list:
        dv_id = dv["dv_id"]
        dv_dict = {
            "dvid": dv_id, "name": dv["dv_name"],
            "value_type": getattr(EnumSecsDataType, dv["value_type"]).value,
            "base_value_type": getattr(EnumSecsDataType, dv["base_value_type"]).value,
            "value": common_func.parse_value(dv["value"], dv["value_type"])
        }
        dv_list_return.append({dv_id: gem.DataValue(**dv_dict)})
    return dv_list_return


def get_ec_list(mysql: MySQLDatabase) -> list[dict[int, gem.EquipmentConstant]]:
    """获取所有的 ec.

    Args:
        mysql: 数据库实例对象.

    Returns:
        list[dict[int, gem.EquipmentConstant]]: 返回 ec 列表.
    """
    ec_list = mysql.query_data(models_class.EcList)
    ec_list_return = []
    for ec in ec_list:
        ec_id = ec["ec_id"]
        ec_value = common_func.parse_value(ec["value"], ec["value_type"])
        ec_dict = {
            "ecid": ec_id, "name": ec["ec_name"], "unit": "",
            "min_value": 0, "max_value": 0, "default_value": ec_value,
            "value_type": getattr(EnumSecsDataType, ec["value_type"]).value
        }
        ec_list_return.append({ec_id: gem.EquipmentConstant(**ec_dict)})
    return ec_list_return


def get_event_list(mysql: MySQLDatabase) -> list[dict[int, gem.CollectionEvent]]:
    """获取所有的事件, 同时关联自定义的报告.

    Args:
        mysql: 数据库实例对象.

    Returns:
        list[dict[int, gem.CollectionEvent]]: 返回事件列表.
    """
    event_list = mysql.query_data(models_class.EventList)  # 获取定义好的事件数据
    event_list_return = []
    for event in event_list:  # 遍历所有的事件
        event_id = event["event_id"]
        associate_report_id_str = event["associate_report"]
        if associate_report_id_str:  # 事件关联了报告
            associate_report_id = int(associate_report_id_str)
            report_info = mysql.query_data(models_class.ReportList, {"report_id": associate_report_id})[0]
            associate_sv_dv = report_info["associate_sv_dv"].split(",")
            link_reports = {associate_report_id: [int(_) for _ in associate_sv_dv if _]}
        else:
            link_reports = {}
        event_dict = {
            "ceid": event_id, "name": event["event_name"], "data_values": [],
            "link_reports": link_reports, "state": event["state"]
        }
        event_list_return.append({event_id: gem.CollectionEvent(**event_dict)})
    return event_list_return


def get_event_link_report(mysql: MySQLDatabase) -> list[dict[int, gem.CollectionEventLink]]:
    """获取工厂定义的事件关联报告.

    Args:
        mysql: 数据库实例对象.

    Returns:
        list[dict[int: CollectionEventLink]]: 工厂定义的事件关联报告.
    """
    event_link_report_list = mysql.query_data(models_class.ReportLinkEvent)  # 工厂定义的事件关联报告
    event_link_report_list_return = []
    for event_link_report in event_link_report_list:
        event_id = event_link_report["event_id"]
        event_info = mysql.query_data(models_class.EventList, {"event_id": event_id})[0]
        event_instance = gem.CollectionEvent(event_id, event_info["event_name"], [])
        event_state = event_link_report["state"]
        report_ids_str = event_link_report["report_ids"]
        report_list = []
        if report_ids_str:
            report_list += [int(report_id) for report_id in report_ids_str.split(",")]
        event_link_report_list_return.append({
            event_id: gem.CollectionEventLink(event_instance, report_list, enabled=event_state)
        })
    return event_link_report_list_return


def get_define_report(mysql: MySQLDatabase) -> list[dict[int, gem.CollectionEventReport]]:
    """获取工厂定义的报告.

    Args:
        mysql: 数据库实例对象.

    Returns:
        list[dict[int, CollectionEventReport]]: 工厂定义的报告.
    """
    define_report_list = mysql.query_data(models_class.DefineReport)
    define_report_list_return = []
    for define_report in define_report_list:
        report_id = define_report["report_id"]
        if variable_ids_str := define_report["variable_ids"]:
            vid_list = [int(vid) for vid in variable_ids_str.split(",")]
        else:
            vid_list = []
        collect_event_report_instance = gem.CollectionEventReport(report_id, vid_list)
        define_report_list_return.append({report_id: collect_event_report_instance})
    return define_report_list_return


def get_enabled_alarm(mysql: MySQLDatabase) -> list[int]:
    """获取工厂已经启用的报警.

    Args:
        mysql: 数据库实例对象.

    Returns:
        list[int]: 工厂已经启用的报警.
    """
    alarm_list = mysql.query_data(models_class.AlarmEnabled)
    if alarm_list:
        return [alarm["alarm_id"] for alarm in alarm_list]
    return alarm_list


def get_event_id_with_name(mysql: MySQLDatabase, event_name: str) -> int:
    """根据事件名称获取事件 id.

    Args:
        mysql: 数据库实例对象.
        event_name: 事件名称.

    Returns:
        int: 事件 id.
    """
    event_list = mysql.query_data(models_class.EventList, {"event_name": event_name})
    if event_list:
        return event_list[0]["event_id"]
    return 0


def get_event_state(mysql: MySQLDatabase, event_id: int) -> int:
    """获取事件的启用停用状态.

    Args:
        mysql: 数据库实例对象.
        event_id: 事件 id.

    Returns:
        int: 事件启用停用状态.
    """
    event_list = mysql.query_data(models_class.EventList, {"event_id": event_id})
    return event_list[0]["state"]


def get_remote_command_list(mysql: MySQLDatabase) -> list[dict[str, gem.RemoteCommand]]:
    """获取所有的远程命令.

    Args:
        mysql: 数据库实例对象.

    Returns:
        list[dict[str, gem.RemoteCommand]]: 返回远程命令列表.
    """
    rc_list = mysql.query_data(models_class.RemoteCommandList)
    rc_list_return = []
    for rc in rc_list:
        rcmd = rc["remote_command"]
        params = rc["parameters"].split(",") if rc["parameters"] else []
        rc_dict = {
            "rcmd": rcmd, "name": rcmd, "params": params, "ce_finished": ""
        }
        rc_list_return.append({rcmd: gem.RemoteCommand(**rc_dict)})
    return rc_list_return


def get_alarm_list(mysql: MySQLDatabase) -> list[dict[str, gem.Alarm]]:
    """获取所有的报警.

    Args:
        mysql: 数据库实例.

    Returns:
        list[dict[str, gem.Alarm]]: 返回报警列表.
    """
    alarm_list = mysql.query_data(models_class.AlarmList)
    alarm_list_return = []
    for alarm in alarm_list:
        alid = alarm["alarm_id"]
        alarm_dict = {
            "alid": alid, "name": alid, "text": alarm["alarm_text_en"], "enabled": True,
            "code": 0, "ce_on": "", "ce_off": "", "text_zh": alarm["alarm_text_zh"]
        }
        alarm_list_return.append({alid: gem.Alarm(**alarm_dict)})
    return alarm_list_return


def get_recipe_name_with_id(mysql: MySQLDatabase, recipe_id: int) -> str:
    """根据配方 id 获取配方名称.

    Args:
        mysql: 数据库实例.
        recipe_id: 配方id.

    Returns:
        str: 返回配方名称.
    """
    recipe_list = mysql.query_data(models_class.RecipeInfo)
    for recipe in recipe_list:
        if recipe["recipe_id"] == recipe_id:
            return recipe["recipe_name"]
    return ""


def get_recipe_id_with_name(mysql: MySQLDatabase, recipe_name: str) -> int:
    """根据配方名称获取配方 id.

    Args:
        mysql: 数据库实例.
        recipe_name: 配方名称.

    Returns:
        int: 返回配方 id.
    """
    recipe_list = mysql.query_data(models_class.RecipeInfo)
    for recipe in recipe_list:
        if recipe["recipe_name"] == recipe_name:
            return recipe["recipe_id"]
    return 0


def get_plc_type(mysql: MySQLDatabase) -> str:
    """获取 plc 类型.

    Args:
        mysql: 数据库实例.

    Returns:
        str: 返回 plc 类型.
    """
    plc_type = mysql.query_data(models_class.EcList, {"ec_name": "plc_type"})[0]["value"]
    return plc_type
