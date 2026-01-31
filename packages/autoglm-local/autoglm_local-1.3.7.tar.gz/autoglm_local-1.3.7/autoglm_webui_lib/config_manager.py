#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块 - 管理 API 配置、场景、历史记录
作者: chenwenkun
"""

import json
import os
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.server_url = ""  # 服务端地址，用于同步历史记录
        os.makedirs(data_dir, exist_ok=True)
        
        # 历史记录分文件存储
        self.history_dir = os.path.join(data_dir, "history")
        self.history_index_file = os.path.join(data_dir, "history_index.json")
        self.reports_dir = os.path.join(data_dir, "reports")
        # 截图文件存储目录
        self.screenshots_dir = os.path.join(data_dir, "screenshots")
        os.makedirs(self.history_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # 兼容旧版 history.json，自动迁移
        self.old_history_file = os.path.join(data_dir, "history.json")
        self._migrate_old_history()
        
        self.api_config_file = os.path.join(data_dir, "api_configs.json")
        self.scenarios_file = os.path.join(data_dir, "scenarios.json")
        self.ios_wda_config_file = os.path.join(data_dir, "ios_wda_configs.json")
    
    def _migrate_old_history(self):
        """迁移旧版 history.json 到分文件存储"""
        if os.path.exists(self.old_history_file):
            try:
                with open(self.old_history_file, "r", encoding="utf-8") as f:
                    old_history = json.load(f)
                
                if old_history and isinstance(old_history, list):
                    for record in old_history:
                        record_id = record.get("id")
                        if record_id:
                            # 保存详情文件
                            detail_file = os.path.join(self.history_dir, f"{record_id}.json")
                            if not os.path.exists(detail_file):
                                with open(detail_file, "w", encoding="utf-8") as f:
                                    json.dump(record, f, ensure_ascii=False, indent=2)
                    
                    # 更新索引
                    self._rebuild_history_index()
                    
                    # 备份并删除旧文件
                    backup_file = self.old_history_file + ".migrated"
                    shutil.move(self.old_history_file, backup_file)
            except Exception as e:
                print(f"迁移历史记录失败: {e}")
    
    def _load_json(self, filepath: str, default: Any = None) -> Any:
        """加载 JSON 文件"""
        if default is None:
            default = []
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return default
    
    def _save_json(self, filepath: str, data: Any):
        """保存 JSON 文件"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    # ============== 截图文件存储 ==============
    
    def save_screenshot(self, batch_id: str, case_id: str, step: int, base64_data: str) -> str:
        """保存截图到文件，返回相对路径
        
        Args:
            batch_id: 批次 ID
            case_id: 用例 ID
            step: 步骤号
            base64_data: base64 编码的图片数据
            
        Returns:
            相对路径，如 screenshots/batch_id/case_id_step_1.png
        """
        import base64
        
        # 创建批次目录
        batch_dir = os.path.join(self.screenshots_dir, batch_id)
        os.makedirs(batch_dir, exist_ok=True)
        
        # 生成文件名
        filename = f"{case_id}_step_{step}.png"
        filepath = os.path.join(batch_dir, filename)
        
        # 解码并保存图片
        try:
            image_data = base64.b64decode(base64_data)
            with open(filepath, "wb") as f:
                f.write(image_data)
            
            # 返回相对路径（用于 URL）
            return f"screenshots/{batch_id}/{filename}"
        except Exception as e:
            print(f"保存截图失败: {e}")
            return ""
    
    def get_screenshot_path(self, relative_path: str) -> str:
        """获取截图的完整文件路径"""
        return os.path.join(self.data_dir, relative_path)
    
    def delete_batch_screenshots(self, batch_id: str):
        """删除批次的所有截图"""
        batch_dir = os.path.join(self.screenshots_dir, batch_id)
        if os.path.exists(batch_dir):
            shutil.rmtree(batch_dir)
    
    # ============== 历史记录（分文件存储） ==============
    
    def _rebuild_history_index(self):
        """重建历史索引"""
        index = []
        if os.path.exists(self.history_dir):
            for filename in os.listdir(self.history_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(self.history_dir, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            record = json.load(f)
                        # 索引只存摘要
                        index.append({
                            "id": record.get("id"),
                            "name": record.get("name", ""),
                            "scenario_name": record.get("scenario_name", ""),
                            "status": record.get("status"),
                            "total_cases": record.get("total_cases"),
                            "completed_cases": record.get("completed_cases"),
                            "start_time": record.get("start_time"),
                            "end_time": record.get("end_time"),
                        })
                    except:
                        pass
        
        # 按时间排序，最新在前
        index.sort(key=lambda x: x.get("start_time") or "", reverse=True)
        self._save_json(self.history_index_file, index)
        return index
    
    def load_history(self) -> List[Dict]:
        """加载历史记录索引（不含详情）"""
        index = self._load_json(self.history_index_file, [])
        if not index:
            # 索引不存在，重建
            index = self._rebuild_history_index()
        return index
    
    def get_history_detail(self, record_id: str) -> Optional[Dict]:
        """获取历史记录详情"""
        detail_file = os.path.join(self.history_dir, f"{record_id}.json")
        if os.path.exists(detail_file):
            return self._load_json(detail_file, None)
        return None
    
    def add_history_record(self, batch_id: str, batch_status: Dict, scenario_name: str = ""):
        """添加历史记录（分文件存储）"""
        # 生成记录名称（使用可读的时间格式）
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if scenario_name:
            name = f"{scenario_name} ({timestamp})"
        else:
            name = f"测试 {timestamp}"
        
        record = {
            "id": batch_id,
            "name": name,
            "scenario_name": scenario_name,
            "status": batch_status.get("status"),
            "total_cases": batch_status.get("total_cases"),
            "completed_cases": batch_status.get("completed_cases"),
            "start_time": batch_status.get("start_time"),
            "end_time": batch_status.get("end_time"),
            "case_results": batch_status.get("case_results", []),
        }
        
        # 保存详情文件
        detail_file = os.path.join(self.history_dir, f"{batch_id}.json")
        self._save_json(detail_file, record)
        
        # 更新索引
        index = self.load_history()
        # 移除已存在的同 ID 记录
        index = [r for r in index if r.get("id") != batch_id]
        # 添加摘要到索引
        index.insert(0, {
            "id": batch_id,
            "name": name,
            "scenario_name": scenario_name,
            "status": record["status"],
            "total_cases": record["total_cases"],
            "completed_cases": record["completed_cases"],
            "start_time": record["start_time"],
            "end_time": record["end_time"],
        })
        # 只保留最近 500 条索引
        index = index[:500]
        self._save_json(self.history_index_file, index)
        
        # 同步到服务端（如果配置了）
        self._sync_history_to_server(record)
    
    def _sync_history_to_server(self, record: Dict):
        """同步历史记录到服务端"""
        if not self.server_url:
            return
        
        try:
            import httpx
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{self.server_url}/history",
                    json=record
                )
                if response.status_code == 200:
                    print(f"✅ 历史记录已同步到服务端: {record.get('id')}")
        except Exception as e:
            print(f"⚠️ 同步历史记录失败: {e}")
    
    def save_history_direct(self, record_id: str, record: Dict):
        """直接保存历史记录（服务端用，不重新生成name）"""
        # 保存详情文件
        detail_file = os.path.join(self.history_dir, f"{record_id}.json")
        self._save_json(detail_file, record)
        
        # 更新索引
        index = self.load_history()
        # 移除已存在的同 ID 记录
        index = [r for r in index if r.get("id") != record_id]
        # 添加摘要到索引（使用本地端发送的数据）
        index.insert(0, {
            "id": record_id,
            "name": record.get("name", ""),
            "scenario_name": record.get("scenario_name", ""),
            "status": record.get("status"),
            "total_cases": record.get("total_cases"),
            "completed_cases": record.get("completed_cases"),
            "start_time": record.get("start_time"),
            "end_time": record.get("end_time"),
        })
        index = index[:500]
        self._save_json(self.history_index_file, index)

    def delete_history(self, record_id: str) -> bool:
        """删除历史记录"""
        # 删除详情文件
        detail_file = os.path.join(self.history_dir, f"{record_id}.json")
        if os.path.exists(detail_file):
            os.remove(detail_file)
        
        # 更新索引
        index = self.load_history()
        new_index = [r for r in index if r.get("id") != record_id]
        self._save_json(self.history_index_file, new_index)
        return len(new_index) < len(index)
    
    # ============== 测试报告生成 ==============
    
    def generate_report(self, record_ids: List[str], report_name: str = "") -> str:
        """生成测试报告 HTML，返回报告 ID"""
        import uuid
        
        report_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if not report_name:
            report_name = f"AI-UI测试报告_{timestamp}"
        
        # 收集所有记录
        records = []
        for rid in record_ids:
            detail = self.get_history_detail(rid)
            if detail:
                records.append(detail)
        
        if not records:
            return None
        
        # 生成 HTML 报告
        html_content = self._generate_report_html(records, report_name, timestamp, report_id)
        
        # 保存报告
        report_file = os.path.join(self.reports_dir, f"{report_id}.html")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # 保存报告元数据
        meta_file = os.path.join(self.reports_dir, f"{report_id}.json")
        meta = {
            "id": report_id,
            "name": report_name,
            "created_at": datetime.now().isoformat(),
            "record_ids": record_ids,
            "total_records": len(records),
        }
        self._save_json(meta_file, meta)
        
        return report_id
    
    def _format_datetime(self, iso_str: str) -> str:
        """格式化时间为 年-月-日 时:分:秒"""
        if not iso_str:
            return "-"
        try:
            if "T" in iso_str:
                dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(iso_str)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return iso_str[:19].replace("T", " ") if len(iso_str) >= 19 else iso_str
    
    def _generate_report_html(self, records: List[Dict], report_name: str, timestamp: str, report_id: str = "") -> str:
        """生成测试报告 HTML 内容 - 专业简洁风格，支持上传到服务器"""
        # 格式化生成时间
        formatted_timestamp = timestamp.replace("_", " ").replace(":", ":")
        if len(formatted_timestamp) == 15:  # 20260121_174226 格式
            formatted_timestamp = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[9:11]}:{timestamp[11:13]}:{timestamp[13:15]}"
        
        # 收集所有用例结果
        all_case_results = []
        for record in records:
            scenario = record.get("scenario_name") or record.get("name", "")
            for case in record.get("case_results", []):
                case_copy = dict(case)
                case_copy["_scenario"] = scenario
                all_case_results.append(case_copy)
        
        # 统计数据（按用例统计）
        total_cases = len(all_case_results)
        success_count = sum(1 for c in all_case_results if c.get("status") == "success")
        failed_count = sum(1 for c in all_case_results if c.get("status") == "failed")
        stopped_count = total_cases - success_count - failed_count
        pass_rate = round(success_count / total_cases * 100, 1) if total_cases > 0 else 0
        
        # 生成用例 JSON 数据（用于前端渲染）- 增加 caseId 用于上传
        import json
        
        def get_screenshot_url(case):
            """获取截图的URL（而不是base64）"""
            screenshots = case.get("screenshots", [])
            if not screenshots:
                return None
            last_screenshot = screenshots[-1]
            image_data = last_screenshot.get("image", "")
            # 如果是文件路径格式（screenshots/xxx/xxx.png），转换为完整URL
            if image_data and image_data.startswith("screenshots/"):
                return image_data  # 前端会处理成完整URL
            # 如果是 base64，返回 None（不上传base64）
            return None
        
        def get_screenshot_for_display(case):
            """获取用于显示的截图（base64或路径）"""
            screenshots = case.get("screenshots", [])
            if not screenshots:
                return None
            return screenshots[-1].get("image")
        
        cases_json = json.dumps([{
            "index": i + 1,
            "caseId": case.get("case_id", f"case_{i}"),
            "scenario": case.get("_scenario", "-"),
            "name": case.get("case_name", "-"),
            "status": case.get("status", "unknown"),
            "result": case.get("result", "-"),
            "end_time": self._format_datetime(case.get("end_time", "")),
            "screenshot": get_screenshot_for_display(case),  # 用于页面显示
            "screenshotPath": get_screenshot_url(case),  # 用于上传到服务器的路径
            "serverId": None  # 服务器返回的 ID，用于更新和删除
        } for i, case in enumerate(all_case_results)], ensure_ascii=False)
        
        # 截图服务器地址（用于生成截图URL，需要是远程服务器可访问的地址）
        screenshot_server_url = "http://qa.local:8792"
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_name}</title>
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect fill='%233b82f6' rx='15' width='100' height='100'/><text x='50' y='68' font-size='50' text-anchor='middle' fill='white'>📊</text></svg>">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-tertiary: #f1f5f9;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            --border: #e2e8f0;
            --success: #10b981;
            --success-bg: #ecfdf5;
            --danger: #ef4444;
            --danger-bg: #fef2f2;
            --warning: #f59e0b;
            --warning-bg: #fffbeb;
            --primary: #3b82f6;
            --primary-bg: #eff6ff;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-secondary);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 100%;
            margin: 0;
            background: var(--bg-primary);
            min-height: 100vh;
        }}
        
        /* Header */
        .header {{
            background: var(--bg-primary);
            border-bottom: 1px solid var(--border);
            padding: 24px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        
        .header-left h1 {{
            font-size: 20px;
            font-weight: 600;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .header-left h1 svg {{
            width: 24px;
            height: 24px;
            color: var(--primary);
        }}
        
        .header-meta {{
            font-size: 13px;
            color: var(--text-secondary);
            margin-top: 4px;
        }}
        
        .header-right {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .pass-rate {{
            background: var(--success-bg);
            color: var(--success);
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
        }}
        
        /* Stats */
        .stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            padding: 24px 32px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border);
        }}
        
        .stat-card {{
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .stat-card:hover {{
            border-color: var(--primary);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
        }}
        
        .stat-card.active {{
            border-color: var(--primary);
            background: var(--primary-bg);
        }}
        
        .stat-card .stat-value {{
            font-size: 32px;
            font-weight: 700;
            color: var(--text-primary);
        }}
        
        .stat-card .stat-label {{
            font-size: 13px;
            color: var(--text-secondary);
            margin-top: 4px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        
        .stat-card.success .stat-value {{ color: var(--success); }}
        .stat-card.failed .stat-value {{ color: var(--danger); }}
        .stat-card.stopped .stat-value {{ color: var(--warning); }}
        
        /* Content */
        .content {{
            padding: 24px 32px;
        }}
        
        .toolbar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }}
        
        .toolbar h2 {{
            font-size: 16px;
            font-weight: 600;
            color: var(--text-primary);
        }}
        
        .toolbar-hint {{
            font-size: 12px;
            color: var(--text-muted);
        }}
        
        /* Table */
        .table-container {{
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        
        th {{
            background: var(--bg-secondary);
            padding: 14px 16px;
            text-align: left;
            font-weight: 600;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border);
            position: sticky;
            top: 0;
        }}
        
        td {{
            padding: 16px;
            border-bottom: 1px solid var(--border);
            vertical-align: top;
        }}
        
        tr:last-child td {{ border-bottom: none; }}
        
        tr.case-row {{
            transition: background 0.15s ease;
        }}
        
        tr.case-row:hover {{
            background: var(--bg-tertiary);
        }}
        
        tr.case-row.success {{ background: var(--success-bg); }}
        tr.case-row.failed {{ background: var(--danger-bg); }}
        tr.case-row.stopped {{ background: var(--warning-bg); }}
        tr.case-row.hidden {{ display: none; }}
        
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
        }}
        
        .status-badge.success {{ background: var(--success-bg); color: var(--success); }}
        .status-badge.failed {{ background: var(--danger-bg); color: var(--danger); }}
        .status-badge.stopped {{ background: var(--warning-bg); color: var(--warning); }}
        
        .result-cell {{
            max-width: 400px;
            color: var(--text-secondary);
            line-height: 1.5;
        }}
        
        .time-cell {{
            white-space: nowrap;
            color: var(--text-muted);
            font-size: 12px;
        }}
        
        /* Screenshot */
        .screenshot-thumb {{
            width: 48px;
            height: 80px;
            object-fit: cover;
            border-radius: 6px;
            border: 1px solid var(--border);
            cursor: pointer;
            transition: transform 0.2s ease;
        }}
        
        .screenshot-thumb:hover {{
            transform: scale(1.05);
        }}
        
        .no-screenshot {{
            color: var(--text-muted);
            font-size: 12px;
        }}
        
        /* Report Upload Actions */
        .report-actions {{
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 20px 32px;
            background: var(--bg-tertiary);
            border-bottom: 1px solid var(--border);
        }}
        
        .report-actions .btn {{
            padding: 12px 24px;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            border: none;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        
        .report-actions .btn-upload {{
            background: linear-gradient(135deg, var(--primary) 0%, #2563eb 100%);
            color: white;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        }}
        
        .report-actions .btn-upload:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
        }}
        
        .report-actions .btn-update {{
            background: linear-gradient(135deg, var(--success) 0%, #059669 100%);
            color: white;
            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
        }}
        
        .report-actions .btn-update:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
        }}
        
        .report-actions .btn-delete {{
            background: linear-gradient(135deg, var(--danger) 0%, #dc2626 100%);
            color: white;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
        }}
        
        .report-actions .btn-delete:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
        }}
        
        .report-actions .btn:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
            transform: none !important;
        }}
        
        .upload-progress {{
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        
        .progress-bar {{
            height: 8px;
            background: var(--border);
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--primary) 0%, var(--success) 100%);
            border-radius: 4px;
            transition: width 0.3s ease;
            width: 0%;
        }}
        
        .progress-text {{
            font-size: 12px;
            color: var(--text-secondary);
        }}
        
        .upload-summary {{
            display: flex;
            align-items: center;
            gap: 16px;
            font-size: 13px;
            color: var(--text-secondary);
        }}
        
        .summary-item {{
            display: flex;
            align-items: center;
            gap: 4px;
        }}
        
        .summary-item.uploaded {{
            color: var(--success);
        }}
        
        .summary-item.pending {{
            color: var(--text-muted);
        }}
        
        /* Modal */
        .modal-overlay {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }}
        
        .modal-overlay.show {{
            display: flex;
        }}
        
        .modal-image {{
            max-width: 90vw;
            max-height: 90vh;
            border-radius: 8px;
        }}
        
        /* Load More */
        .load-more {{
            padding: 20px;
            text-align: center;
            border-top: 1px solid var(--border);
        }}
        
        .load-more-btn {{
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 12px 24px;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        
        .load-more-btn:hover {{
            background: var(--bg-tertiary);
            border-color: var(--primary);
            color: var(--primary);
        }}
        
        .load-more-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        
        /* Footer */
        .footer {{
            padding: 20px 32px;
            background: var(--bg-secondary);
            border-top: 1px solid var(--border);
            text-align: center;
            font-size: 12px;
            color: var(--text-muted);
        }}
        
        @media (max-width: 768px) {{
            .stats {{ grid-template-columns: repeat(2, 1fr); }}
            .header {{ flex-direction: column; align-items: flex-start; gap: 12px; }}
            .result-cell {{ max-width: 200px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <div class="header-left">
                <h1>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/>
                        <rect x="9" y="3" width="6" height="4" rx="1"/>
                        <path d="M9 12l2 2 4-4"/>
                    </svg>
                    {report_name}
                </h1>
                <div class="header-meta">生成时间：{formatted_timestamp}</div>
            </div>
            <div class="header-right">
                <div class="pass-rate">通过率 {pass_rate}%</div>
            </div>
        </header>
        
        <div class="stats">
            <div class="stat-card active" onclick="filterCases('all')" id="card-all">
                <div class="stat-value">{total_cases}</div>
                <div class="stat-label">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="3" y="3" width="18" height="18" rx="2"/>
                        <path d="M3 9h18M9 21V9"/>
                    </svg>
                    全部用例
                </div>
            </div>
            <div class="stat-card success" onclick="filterCases('success')" id="card-success">
                <div class="stat-value">{success_count}</div>
                <div class="stat-label">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>
                    成功
                </div>
            </div>
            <div class="stat-card failed" onclick="filterCases('failed')" id="card-failed">
                <div class="stat-value">{failed_count}</div>
                <div class="stat-label">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="15" y1="9" x2="9" y2="15"/>
                        <line x1="9" y1="9" x2="15" y2="15"/>
                    </svg>
                    失败
                </div>
            </div>
            <div class="stat-card stopped" onclick="filterCases('stopped')" id="card-stopped">
                <div class="stat-value">{stopped_count}</div>
                <div class="stat-label">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="10" y1="15" x2="10" y2="9"/>
                        <line x1="14" y1="15" x2="14" y2="9"/>
                    </svg>
                    中断
                </div>
            </div>
        </div>
        
        <div class="report-actions">
            <button class="btn btn-upload" id="uploadReportBtn" onclick="uploadReport()">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                    <polyline points="17 8 12 3 7 8"/>
                    <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                上传报告到服务器
            </button>
            <button class="btn btn-update" id="updateReportBtn" onclick="updateReport()" style="display:none;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M23 4v6h-6"/>
                    <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
                </svg>
                更新报告
            </button>
            <button class="btn btn-delete" id="deleteReportBtn" onclick="deleteReport()" style="display:none;">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                </svg>
                删除报告
            </button>
            
            <div class="upload-progress" id="uploadProgress" style="display:none;">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="progress-text" id="progressText">准备上传...</div>
            </div>
            
            <div class="upload-summary" id="uploadSummary">
                <span class="summary-item uploaded" id="uploadedCount">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>
                    已上传: <strong>0</strong> 条
                </span>
                <span class="summary-item pending" id="pendingCount">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 6 12 12 16 14"/>
                    </svg>
                    待上传: <strong>{total_cases}</strong> 条
                </span>
            </div>
        </div>
        
        <div class="content">
            <div class="toolbar">
                <h2>测试结果详情</h2>
                <span class="toolbar-hint">点击统计卡片筛选 · 点击截图放大</span>
            </div>
            
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th style="width:50px">#</th>
                            <th style="width:120px">场景</th>
                            <th>用例名称</th>
                            <th style="width:80px">状态</th>
                            <th>执行结果</th>
                            <th style="width:160px">完成时间</th>
                            <th style="width:70px">截图</th>
                            <th style="width:80px">上传状态</th>
                        </tr>
                    </thead>
                    <tbody id="caseTableBody">
                    </tbody>
                </table>
                
                <div class="load-more" id="loadMoreSection">
                    <button class="load-more-btn" onclick="loadMore()" id="loadMoreBtn">
                        加载更多
                    </button>
                </div>
            </div>
        </div>
        
        <footer class="footer">
            AI-APPUI 自动化测试平台 · 作者: chenwenkun
        </footer>
    </div>
    
    <!-- 图片预览弹窗 -->
    <div class="modal-overlay" id="imageModal" onclick="closeModal()">
        <img class="modal-image" id="modalImage" src="" alt="截图预览">
    </div>
    
    <script>
        const allCases = {cases_json};
        let currentFilter = 'all';
        let displayCount = 10;
        const PAGE_SIZE = 10;
        
        // 服务器API配置（使用本地代理接口解决CORS问题）
        const UPLOAD_URL = '/api/proxy/case-result/insertOrUpdate';
        const DELETE_URL = '/api/proxy/case-result/deleteById';
        // 截图服务器地址（用于生成截图URL）
        const SCREENSHOT_SERVER_URL = '{screenshot_server_url}';
        
        // 从 localStorage 加载已上传的记录 (使用报告ID作为唯一标识)
        const REPORT_ID = '{report_id}';
        const STORAGE_KEY = 'uploaded_cases_' + REPORT_ID;
        let uploadedCases = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{}}');
        
        // 恢复已上传的 serverId
        allCases.forEach(c => {{
            if (uploadedCases[c.caseId]) {{
                c.serverId = uploadedCases[c.caseId];
            }}
        }});
        
        function getFilteredCases() {{
            if (currentFilter === 'all') return allCases;
            return allCases.filter(c => c.status === currentFilter);
        }}
        
        function saveUploadedCases() {{
            const data = {{}};
            allCases.forEach(c => {{
                if (c.serverId) {{
                    data[c.caseId] = c.serverId;
                }}
            }});
            localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
        }}
        
        function updateUploadSummary() {{
            const uploadedCount = allCases.filter(c => c.serverId).length;
            const pendingCount = allCases.length - uploadedCount;
            
            document.querySelector('#uploadedCount strong').textContent = uploadedCount;
            document.querySelector('#pendingCount strong').textContent = pendingCount;
            
            // 更新按钮显示状态
            const uploadBtn = document.getElementById('uploadReportBtn');
            const updateBtn = document.getElementById('updateReportBtn');
            const deleteBtn = document.getElementById('deleteReportBtn');
            
            if (uploadedCount === 0) {{
                // 未上传任何用例
                uploadBtn.style.display = 'inline-flex';
                updateBtn.style.display = 'none';
                deleteBtn.style.display = 'none';
            }} else if (uploadedCount === allCases.length) {{
                // 全部已上传
                uploadBtn.style.display = 'none';
                updateBtn.style.display = 'inline-flex';
                deleteBtn.style.display = 'inline-flex';
            }} else {{
                // 部分上传
                uploadBtn.style.display = 'inline-flex';
                uploadBtn.innerHTML = `
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                        <polyline points="17 8 12 3 7 8"/>
                        <line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                    继续上传 (${{pendingCount}}条)
                `;
                updateBtn.style.display = 'inline-flex';
                deleteBtn.style.display = 'inline-flex';
            }}
        }}
        
        function renderCases() {{
            const filtered = getFilteredCases();
            const toShow = filtered.slice(0, displayCount);
            const tbody = document.getElementById('caseTableBody');
            
            tbody.innerHTML = toShow.map(c => {{
                const statusClass = c.status === 'success' ? 'success' : c.status === 'failed' ? 'failed' : 'stopped';
                const statusText = c.status === 'success' ? '成功' : c.status === 'failed' ? '失败' : '中断';
                // 截图可能是文件路径（新格式）或 base64（旧格式）
                let screenshotHtml = '<span class="no-screenshot">-</span>';
                if (c.screenshot) {{
                    // 判断是否为文件路径（包含 screenshots/）
                    const imgSrc = c.screenshot.startsWith('screenshots/') 
                        ? `/data/${{c.screenshot}}`  // 使用 URL 访问
                        : `data:image/png;base64,${{c.screenshot}}`;  // 兼容旧的 base64 格式
                    screenshotHtml = `<img src="${{imgSrc}}" class="screenshot-thumb" onclick="event.stopPropagation();showImage(this.src)">`;
                }}
                
                // 上传状态显示
                const hasServerId = c.serverId != null;
                const uploadStatusHtml = hasServerId 
                    ? `<span style="color:var(--success);font-size:12px;">✓ 已上传</span>`
                    : `<span style="color:var(--text-muted);font-size:12px;">待上传</span>`;
                
                return `
                    <tr class="case-row ${{statusClass}}" data-index="${{c.index - 1}}">
                        <td>${{c.index}}</td>
                        <td>${{c.scenario}}</td>
                        <td>${{c.name}}</td>
                        <td><span class="status-badge ${{statusClass}}">${{statusText}}</span></td>
                        <td class="result-cell">${{c.result}}</td>
                        <td class="time-cell">${{c.end_time}}</td>
                        <td>${{screenshotHtml}}</td>
                        <td id="upload-status-${{c.index}}">${{uploadStatusHtml}}</td>
                    </tr>
                `;
            }}).join('');
            
            // 更新加载更多按钮
            const loadMoreBtn = document.getElementById('loadMoreBtn');
            if (displayCount >= filtered.length) {{
                loadMoreBtn.textContent = '已加载全部';
                loadMoreBtn.disabled = true;
            }} else {{
                loadMoreBtn.textContent = `加载更多 (${{displayCount}}/${{filtered.length}})`;
                loadMoreBtn.disabled = false;
            }}
            
            updateUploadSummary();
        }}
        
        function filterCases(status) {{
            currentFilter = status;
            displayCount = PAGE_SIZE;
            
            document.querySelectorAll('.stat-card').forEach(card => card.classList.remove('active'));
            document.getElementById('card-' + status).classList.add('active');
            
            renderCases();
        }}
        
        function loadMore() {{
            displayCount += PAGE_SIZE;
            renderCases();
        }}
        
        function showImage(src) {{
            document.getElementById('modalImage').src = src;
            document.getElementById('imageModal').classList.add('show');
        }}
        
        function closeModal() {{
            document.getElementById('imageModal').classList.remove('show');
        }}
        
        // ========== 报告上传功能 ==========
        
        function mapStatusToServer(status) {{
            const statusMap = {{
                'success': '成功',
                'failed': '失败',
                'stopped': '中断',
                'unknown': '未知'
            }};
            return statusMap[status] || status;
        }}
        
        function setButtonsDisabled(disabled) {{
            document.getElementById('uploadReportBtn').disabled = disabled;
            document.getElementById('updateReportBtn').disabled = disabled;
            document.getElementById('deleteReportBtn').disabled = disabled;
        }}
        
        function showProgress(show) {{
            document.getElementById('uploadProgress').style.display = show ? 'flex' : 'none';
        }}
        
        function updateProgress(current, total, text) {{
            const percent = Math.round((current / total) * 100);
            document.getElementById('progressFill').style.width = percent + '%';
            document.getElementById('progressText').textContent = text || `正在处理 ${{current}}/${{total}}...`;
        }}
        
        function getScreenshotUrl(c) {{
            // 将截图路径转换为完整的URL
            if (!c.screenshotPath) {{
                return '';
            }}
            // 如果是相对路径，转换为完整URL
            if (c.screenshotPath.startsWith('screenshots/')) {{
                // 使用配置的截图服务器地址构建完整URL（确保远程服务器可以访问）
                return SCREENSHOT_SERVER_URL + '/data/' + c.screenshotPath;
            }}
            return c.screenshotPath;
        }}
        
        async function uploadSingleCase(c, isUpdate = false) {{
            // 获取截图的完整URL（而不是base64）
            const screenshotUrl = getScreenshotUrl(c);
            
            const payload = {{
                scene: c.scenario || '-',
                resultStatus: mapStatusToServer(c.status),
                caseResult: c.result || '-',
                screenshotUrl: screenshotUrl,
                caseName: c.name || '-'
            }};
            
            // 如果有 serverId，则为更新
            if (c.serverId && isUpdate) {{
                payload.id = c.serverId;
            }}
            
            console.log('上传数据:', payload);  // 调试用
            
            const response = await fetch(UPLOAD_URL, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify(payload)
            }});
            
            const result = await response.json();
            
            if (result.code === 0) {{
                // 提取返回的 ID
                if (result.data && typeof result.data === 'number') {{
                    c.serverId = result.data;
                }} else if (result.data && result.data.id) {{
                    c.serverId = result.data.id;
                }} else if (!c.serverId) {{
                    c.serverId = 'uploaded_' + Date.now() + '_' + c.index;
                }}
                return true;
            }} else {{
                throw new Error(result.message || '上传失败');
            }}
        }}
        
        async function deleteSingleCase(c) {{
            if (!c.serverId) return true;
            
            const response = await fetch(DELETE_URL, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{ id: c.serverId }})
            }});
            
            const result = await response.json();
            
            if (result.code === 0) {{
                c.serverId = null;
                return true;
            }} else {{
                throw new Error(result.message || '删除失败');
            }}
        }}
        
        async function uploadReport() {{
            const pendingCases = allCases.filter(c => !c.serverId);
            
            if (pendingCases.length === 0) {{
                alert('所有用例已上传');
                return;
            }}
            
            if (!confirm(`确定要上传 ${{pendingCases.length}} 条用例到服务器吗？`)) {{
                return;
            }}
            
            setButtonsDisabled(true);
            showProgress(true);
            
            let successCount = 0;
            let failedCount = 0;
            
            for (let i = 0; i < pendingCases.length; i++) {{
                const c = pendingCases[i];
                updateProgress(i + 1, pendingCases.length, `正在上传: ${{c.name}}`);
                
                // 更新表格中的状态
                const statusEl = document.getElementById('upload-status-' + c.index);
                if (statusEl) {{
                    statusEl.innerHTML = '<span style="color:var(--warning);font-size:12px;">上传中...</span>';
                }}
                
                try {{
                    await uploadSingleCase(c);
                    successCount++;
                    if (statusEl) {{
                        statusEl.innerHTML = '<span style="color:var(--success);font-size:12px;">✓ 已上传</span>';
                    }}
                }} catch (e) {{
                    failedCount++;
                    if (statusEl) {{
                        statusEl.innerHTML = `<span style="color:var(--danger);font-size:12px;">✗ 失败</span>`;
                    }}
                    console.error('上传失败:', c.name, e);
                }}
                
                // 间隔100ms避免请求过快
                await new Promise(resolve => setTimeout(resolve, 100));
            }}
            
            saveUploadedCases();
            showProgress(false);
            setButtonsDisabled(false);
            updateUploadSummary();
            renderCases();
            
            if (failedCount === 0) {{
                alert(`上传完成！成功 ${{successCount}} 条`);
            }} else {{
                alert(`上传完成！成功 ${{successCount}} 条，失败 ${{failedCount}} 条`);
            }}
        }}
        
        async function updateReport() {{
            const uploadedCases = allCases.filter(c => c.serverId);
            
            if (uploadedCases.length === 0) {{
                alert('没有已上传的用例需要更新');
                return;
            }}
            
            if (!confirm(`确定要更新 ${{uploadedCases.length}} 条已上传的用例吗？`)) {{
                return;
            }}
            
            setButtonsDisabled(true);
            showProgress(true);
            
            let successCount = 0;
            let failedCount = 0;
            
            for (let i = 0; i < uploadedCases.length; i++) {{
                const c = uploadedCases[i];
                updateProgress(i + 1, uploadedCases.length, `正在更新: ${{c.name}}`);
                
                try {{
                    await uploadSingleCase(c, true);
                    successCount++;
                }} catch (e) {{
                    failedCount++;
                    console.error('更新失败:', c.name, e);
                }}
                
                await new Promise(resolve => setTimeout(resolve, 100));
            }}
            
            saveUploadedCases();
            showProgress(false);
            setButtonsDisabled(false);
            
            if (failedCount === 0) {{
                alert(`更新完成！成功 ${{successCount}} 条`);
            }} else {{
                alert(`更新完成！成功 ${{successCount}} 条，失败 ${{failedCount}} 条`);
            }}
        }}
        
        async function deleteReport() {{
            const uploadedCases = allCases.filter(c => c.serverId);
            
            if (uploadedCases.length === 0) {{
                alert('没有已上传的用例需要删除');
                return;
            }}
            
            if (!confirm(`⚠️ 确定要从服务器删除 ${{uploadedCases.length}} 条用例吗？\\n\\n此操作不可恢复！`)) {{
                return;
            }}
            
            setButtonsDisabled(true);
            showProgress(true);
            
            let successCount = 0;
            let failedCount = 0;
            
            for (let i = 0; i < uploadedCases.length; i++) {{
                const c = uploadedCases[i];
                updateProgress(i + 1, uploadedCases.length, `正在删除: ${{c.name}}`);
                
                // 更新表格中的状态
                const statusEl = document.getElementById('upload-status-' + c.index);
                if (statusEl) {{
                    statusEl.innerHTML = '<span style="color:var(--warning);font-size:12px;">删除中...</span>';
                }}
                
                try {{
                    await deleteSingleCase(c);
                    successCount++;
                    if (statusEl) {{
                        statusEl.innerHTML = '<span style="color:var(--text-muted);font-size:12px;">待上传</span>';
                    }}
                }} catch (e) {{
                    failedCount++;
                    if (statusEl) {{
                        statusEl.innerHTML = `<span style="color:var(--danger);font-size:12px;">✗ 删除失败</span>`;
                    }}
                    console.error('删除失败:', c.name, e);
                }}
                
                await new Promise(resolve => setTimeout(resolve, 100));
            }}
            
            saveUploadedCases();
            showProgress(false);
            setButtonsDisabled(false);
            updateUploadSummary();
            renderCases();
            
            if (failedCount === 0) {{
                alert(`删除完成！成功 ${{successCount}} 条`);
            }} else {{
                alert(`删除完成！成功 ${{successCount}} 条，失败 ${{failedCount}} 条`);
            }}
        }}
        
        // 初始渲染
        renderCases();
    </script>
</body>
</html>"""
        return html
    
    def list_reports(self) -> List[Dict]:
        """列出所有报告"""
        reports = []
        if os.path.exists(self.reports_dir):
            for filename in os.listdir(self.reports_dir):
                if filename.endswith(".json"):
                    meta_file = os.path.join(self.reports_dir, filename)
                    meta = self._load_json(meta_file, None)
                    if meta:
                        reports.append(meta)
        reports.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return reports
    
    def get_report_path(self, report_id: str) -> Optional[str]:
        """获取报告 HTML 文件路径"""
        report_file = os.path.join(self.reports_dir, f"{report_id}.html")
        if os.path.exists(report_file):
            return report_file
        return None
    
    def delete_report(self, report_id: str) -> bool:
        """删除报告"""
        html_file = os.path.join(self.reports_dir, f"{report_id}.html")
        meta_file = os.path.join(self.reports_dir, f"{report_id}.json")
        deleted = False
        if os.path.exists(html_file):
            os.remove(html_file)
            deleted = True
        if os.path.exists(meta_file):
            os.remove(meta_file)
            deleted = True
        return deleted
    
    # ============== API 配置 ==============
    
    def load_api_configs(self) -> List[Dict]:
        """加载 API 配置列表"""
        return self._load_json(self.api_config_file, [])
    
    def save_api_configs(self, configs: List[Dict]):
        """保存 API 配置列表"""
        self._save_json(self.api_config_file, configs)
    
    def add_api_config(self, config: Dict) -> Dict:
        """添加 API 配置"""
        import uuid
        configs = self.load_api_configs()
        config["id"] = str(uuid.uuid4())[:8]
        configs.append(config)
        self.save_api_configs(configs)
        return config
    
    def update_api_config(self, config_id: str, config: Dict) -> bool:
        """更新 API 配置"""
        configs = self.load_api_configs()
        for i, c in enumerate(configs):
            if c["id"] == config_id:
                config["id"] = config_id
                configs[i] = config
                self.save_api_configs(configs)
                return True
        return False
    
    def delete_api_config(self, config_id: str) -> bool:
        """删除 API 配置"""
        configs = self.load_api_configs()
        new_configs = [c for c in configs if c["id"] != config_id]
        self.save_api_configs(new_configs)
        return len(new_configs) < len(configs)
    
    def get_api_config(self, config_id: str) -> Optional[Dict]:
        """获取指定 API 配置"""
        configs = self.load_api_configs()
        for c in configs:
            if c["id"] == config_id:
                return c
        return None
    
    # ============== 场景管理 ==============
    
    def load_scenarios(self) -> List[Dict]:
        """加载场景列表"""
        return self._load_json(self.scenarios_file, [])
    
    def save_scenarios(self, scenarios: List[Dict]):
        """保存场景列表"""
        self._save_json(self.scenarios_file, scenarios)
    
    def add_scenario(self, name: str, test_cases: List[Dict]) -> Dict:
        """添加场景"""
        import uuid
        scenarios = self.load_scenarios()
        scenario = {
            "id": str(uuid.uuid4())[:8],
            "name": name,
            "test_cases": test_cases,
            "created_at": datetime.now().isoformat(),
        }
        scenarios.insert(0, scenario)
        self.save_scenarios(scenarios)
        return scenario
    
    def delete_scenario(self, scenario_id: str) -> bool:
        """删除场景"""
        scenarios = self.load_scenarios()
        new_scenarios = [s for s in scenarios if s["id"] != scenario_id]
        self.save_scenarios(new_scenarios)
        return len(new_scenarios) < len(scenarios)
    
    # ============== iOS WDA 配置 ==============
    
    def load_ios_wda_configs(self) -> Dict:
        """加载 iOS WDA 配置"""
        return self._load_json(self.ios_wda_config_file, {})
    
    def save_ios_wda_configs(self, configs: Dict):
        """保存 iOS WDA 配置"""
        self._save_json(self.ios_wda_config_file, configs)
    
    def set_ios_wda_config(self, device_id: str, wda_url: str):
        """设置 iOS 设备的 WDA URL"""
        configs = self.load_ios_wda_configs()
        configs[device_id] = wda_url.rstrip("/")
        self.save_ios_wda_configs(configs)
    
    def get_ios_wda_config(self, device_id: str) -> Optional[str]:
        """获取 iOS 设备的 WDA URL"""
        configs = self.load_ios_wda_configs()
        return configs.get(device_id)
