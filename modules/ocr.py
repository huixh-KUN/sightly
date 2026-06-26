import asyncio
import threading
import time
from typing import Optional

import imagehash

from PySide6.QtWidgets import QMessageBox

from core.config import safe_group_get
from utils.image import _preprocess_image
from utils.screenshot import ScreenshotManager
from utils.recognition import OCRRecognizer
from core.priority_lock import get_module_priority
from core.click_handler import ClickHandler
from core.async_utils import run_in_executor
from utils.memory import MemoryMonitor


class OCRModule:
    """
    OCR模块，负责文字识别核心逻辑
    优先级: 3 (Number=6 > Timed=5 > Image=4 > OCR=3 > Color=2 > Script=1)
    """

    PRIORITY = get_module_priority('ocr')

    def __init__(self, app):
        self.app = app
        self.last_recognition_times = {}
        self.last_trigger_times = {}
        self.click_handler = ClickHandler(app)
        self.screenshot_manager = ScreenshotManager()
        self.memory_monitor = MemoryMonitor()
        self._last_texts = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

    def start_monitoring(self):
        """开始监控（异步协程版）"""
        self.app.logging_manager.debug("OCR", "start_monitoring 开始")
        if not self.app.tesseract_available:
            self.app.logging_manager.debug("OCR", "Tesseract OCR引擎未配置")
            QMessageBox.information(None, "提示",
                "Tesseract OCR引擎未配置，请在设置中配置Tesseract路径后使用文字识别功能！")
            return

        has_enabled_group = False
        for group in self.app.ocr_groups:
            if group["enabled"].get() and group["region"]:
                has_enabled_group = True
                break

        if not has_enabled_group:
            self.app.logging_manager.debug("OCR", "无已启用的识别组")
            QMessageBox.warning(None, "警告", "请至少启用一个识别组并选择区域")
            return

        self._thread = threading.Thread(target=self._run_async, daemon=True)
        self._thread.start()

    def stop_monitoring(self):
        """停止监控"""
        if self._loop and self._loop.is_running():
            for task in asyncio.all_tasks(loop=self._loop):
                if not task.done():
                    task.cancel()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        self._last_texts.clear()

    def _run_async(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            loop.run_until_complete(self._async_main())
        finally:
            loop.close()
            self._loop = None

    async def _async_main(self):
        tasks = []
        for i, group in enumerate(self.app.ocr_groups):
            if group["enabled"].get() and group["region"]:
                t = asyncio.create_task(self._ocr_group_loop(i, group))
                tasks.append(t)
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                pass
    
    async def _ocr_group_loop(self, group_index, group):
        """单个OCR组的异步识别循环"""
        last_hash = None
        frame_count = 0
        def _get(v, default=None):
            return v.get() if hasattr(v, 'get') else (v if v is not None else default)
        self.app.logging_manager.debug("OCR",
            f"识别组{group_index+1} 协程开始: keywords={_get(group.get('keywords',''))}")
        try:
            while not (self._loop and self._loop.is_closed()):
                try:
                    if not _get(group.get("enabled"), False) or not group.get("region"):
                        await asyncio.sleep(1)
                        continue
                    try:
                        pause_duration = int(_get(group.get("pause"), 180))
                    except (ValueError, TypeError):
                        pause_duration = 180
                    try:
                        group_interval = int(_get(group.get("interval"), 5))
                    except (ValueError, TypeError):
                        group_interval = 5

                    now = time.time()
                    if now - self.last_trigger_times.get(group_index, 0) < pause_duration:
                        await asyncio.sleep(1)
                        continue
                    if now - self.last_recognition_times.get(group_index, 0) < group_interval:
                        await asyncio.sleep(1)
                        continue

                    self.app.logging_manager.debug("OCR",
                        f"识别组{group_index+1} 开始识别: pause={pause_duration}, interval={group_interval}")
                    last_hash, frame_count = await run_in_executor(
                        self._do_ocr_group, group, group_index, last_hash, frame_count
                    )
                    self.last_recognition_times[group_index] = time.time()
                    
                    frame_count += 1
                    if self.memory_monitor.gc_if_needed(frame_count):
                        self.app.logging_manager.debug("OCR", f"识别组{group_index+1} 触发 GC")
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    self.app.logging_manager.error("OCR", f"识别组{group_index+1}错误: {str(e)}")
                    await asyncio.sleep(5)
        except asyncio.CancelledError:
            self.app.logging_manager.debug("OCR", f"识别组{group_index+1} 协程取消")

    def _do_ocr_group(self, group, group_index, last_hash, frame_count):
        """同步执行单个OCR组的识别（在线程池中运行），返回更新后的 (last_hash, frame_count)"""
        lh = {group_index: last_hash}
        fc = {group_index: frame_count}
        self.perform_ocr_for_group_optimized(group, group_index, lh, fc)
        return (lh.get(group_index), fc.get(group_index, 0))


    def _validate_ocr_group_input(self, group, group_index):
        if not group:
            self.app.logging_manager.error("OCR", f"识别组{group_index+1}错误: 组配置为空")
            return False, None, None, None, None

        region = group.get("region")
        if not region:
            self.app.logging_manager.error("OCR", f"识别组{group_index+1}错误: 未设置识别区域")
            return False, None, None, None, None

        keywords_str = safe_group_get(group, "keywords", "").strip()
        current_lang = safe_group_get(group, "language", "简体中文")
        click_enabled = safe_group_get(group, "click", False)
        return True, region, keywords_str, current_lang, click_enabled
    
    def _validate_region_coordinates(self, region, group_index):
        try:
            x1, y1, x2, y2 = region
            if len(region) != 4:
                raise ValueError("区域坐标格式错误")
        except (ValueError, TypeError) as e:
            self.app.logging_manager.error("OCR", f"识别组{group_index+1}错误: 区域坐标无效 - {str(e)}")
            return False, None, None, None, None

        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)

        if (right - left) < 10 or (bottom - top) < 10:
            self.app.logging_manager.error("OCR", f"识别组{group_index+1}错误: 识别区域太小")
            return False, None, None, None, None

        return True, left, top, right, bottom
    
    def _capture_screen_region(self, left, top, right, bottom, group_index):
        try:
            self.app.logging_manager.debug("OCR", f"识别组{group_index+1} 截图请求: ({left},{top})-({right},{bottom})")
            screenshot = self.screenshot_manager.get_region_screenshot((left, top, right, bottom), priority=self.PRIORITY)
            if screenshot:
                self.app.logging_manager.debug("OCR", f"识别组{group_index+1} 截图成功: {screenshot.size}")
            else:
                self.app.logging_manager.debug("OCR", f"识别组{group_index+1} 截图返回 None")
            return screenshot
        except Exception as e:
            self.app.logging_manager.error("OCR", f"识别组{group_index+1}错误: 屏幕截图失败 - {str(e)}")
            self.app.logging_manager.debug("OCR", f"识别组{group_index+1} 截图异常: {e}")
            return None
    
    def _recognize_on_processed_image(
        self, processed_image, group_index, keywords_str, current_lang,
        click_enabled, left, top, right, bottom, *, log_results=True,
    ):
        """在预处理图像上执行 OCR 与关键词匹配，返回识别结果 dict。"""
        result = {
            "matched": False,
            "text": "",
            "click_pos": None,
            "click_enabled": click_enabled,
            "detail": "",
        }
        if keywords_str:
            keywords = [kw.strip().lower() for kw in keywords_str.split(",") if kw.strip()]
            if log_results:
                self.app.logging_manager.log_message(
                    f"识别组{group_index+1}: 开始OCR识别，关键词: {keywords}"
                )
                self.app.logging_manager.debug("OCR", f"识别组{group_index+1} 开始OCR识别")
            text = OCRRecognizer.get_text(processed_image, current_lang)
            result["text"] = text or ""
            if not text:
                result["detail"] = "OCR未识别到文字"
                if log_results:
                    self.app.logging_manager.log_message(f"识别组{group_index+1}: OCR未识别到文字")
                return result
            if log_results:
                last_text = self._last_texts.get(group_index)
                if text.strip() != last_text:
                    self.app.logging_manager.log_message(
                        f"识别组{group_index+1}识别结果: '{text.strip()[:60]}'"
                    )
                    self._last_texts[group_index] = text.strip()
            lower_text = text.lower()
            matched_keywords = [kw for kw in keywords if kw in lower_text]
            if matched_keywords:
                result["matched"] = True
                if click_enabled:
                    rel_pos = OCRRecognizer.find_keyword_position(
                        processed_image, keywords, current_lang
                    )
                    if rel_pos:
                        click_pos = (left + rel_pos[0], top + rel_pos[1])
                    else:
                        click_pos = ((left + right) // 2, (top + bottom) // 2)
                else:
                    click_pos = ((left + right) // 2, (top + bottom) // 2)
                result["click_pos"] = click_pos
                result["detail"] = (
                    f"关键词匹配成功: {matched_keywords}；"
                    f"识别文本: '{text.strip()[:60]}'"
                )
                if log_results:
                    self.app.logging_manager.log_message(
                        f"识别组{group_index+1}: 关键词匹配成功 - {matched_keywords}"
                    )
            else:
                result["detail"] = f"未匹配到关键词；识别文本: '{text.strip()[:60]}'"
        else:
            if log_results:
                self.app.logging_manager.log_message(f"识别组{group_index+1}: 开始OCR识别（无关键词）")
            text = OCRRecognizer.get_text(processed_image, current_lang)
            result["text"] = text or ""
            if text:
                if log_results:
                    last_text = self._last_texts.get(group_index)
                    if text.strip() != last_text:
                        self.app.logging_manager.log_message(
                            f"识别组{group_index+1}识别结果: '{text.strip()[:60]}'"
                        )
                        self._last_texts[group_index] = text.strip()
                result["detail"] = f"识别文本: '{text.strip()[:60]}'（未配置关键词）"
            else:
                result["detail"] = "OCR未识别到文字"
        return result

    def recognize_group_once(self, group, group_index) -> dict:
        """单次识别（无 imagehash 去重、无 is_running 守卫）。"""
        screenshot = None
        processed_image = None
        try:
            valid, region, keywords_str, current_lang, click_enabled = (
                self._validate_ocr_group_input(group, group_index)
            )
            if not valid:
                return {"matched": False, "executed": False, "detail": "组配置无效或未设置识别区域"}
            valid, left, top, right, bottom = self._validate_region_coordinates(region, group_index)
            if not valid:
                return {"matched": False, "executed": False, "detail": "区域坐标无效"}
            screenshot = self._capture_screen_region(left, top, right, bottom, group_index)
            if not screenshot:
                return {"matched": False, "executed": False, "detail": "截图失败"}
            processed_image = _preprocess_image(screenshot, group_index)
            if not processed_image:
                return {"matched": False, "executed": False, "detail": "图像预处理失败"}
            rec = self._recognize_on_processed_image(
                processed_image, group_index, keywords_str, current_lang,
                click_enabled, left, top, right, bottom, log_results=False,
            )
            rec["executed"] = False
            return rec
        except Exception as e:
            self.app.logging_manager.error("OCR", f"识别组{group_index+1}测试识别失败: {e}")
            return {"matched": False, "executed": False, "detail": str(e)}
        finally:
            if processed_image is not None:
                del processed_image
            if screenshot is not None:
                screenshot.close()
                del screenshot

    def execute_group_actions(self, group, group_index, rec_result, *, for_test=False):
        """执行识别匹配后的动作（点击、按键、报警）。"""
        if not rec_result.get("matched"):
            return
        self.trigger_action_for_group(
            group, group_index,
            rec_result.get("click_enabled", False),
            rec_result.get("click_pos"),
            for_test=for_test,
        )

    def test_group(self, index) -> dict:
        groups = getattr(self.app, 'ocr_groups', [])
        if index >= len(groups):
            return {"matched": False, "executed": False, "detail": "组索引越界"}
        group = groups[index]
        rec = self.recognize_group_once(group, index)
        executed = False
        detail = rec.get("detail", "")
        if rec.get("matched"):
            self.execute_group_actions(group, index, rec, for_test=True)
            executed = True
            detail = f"{detail}；已按配置执行动作"
        return {
            "matched": rec.get("matched", False),
            "executed": executed,
            "detail": detail,
        }

    def perform_ocr_for_group_optimized(self, group, group_index, last_hashes, frame_counts):
        """
        为单个OCR组执行OCR识别（优化版本，使用增量截图和自适应帧率）
        """
        screenshot = None
        processed_image = None
        try:
            if not self.app.is_running:
                return

            self.app.logging_manager.debug("OCR", f"识别组{group_index+1} 开始处理")

            valid, region, keywords_str, current_lang, click_enabled = self._validate_ocr_group_input(group, group_index)
            if not valid:
                return

            valid, left, top, right, bottom = self._validate_region_coordinates(region, group_index)
            if not valid:
                return

            self.app.logging_manager.debug("OCR", f"识别组{group_index+1} 区域: ({left},{top})-({right},{bottom})")

            screenshot = self._capture_screen_region(left, top, right, bottom, group_index)
            if not screenshot:
                self.app.logging_manager.error("OCR", f"识别组{group_index+1}: 截图失败或为空")
                self.app.logging_manager.debug("OCR", f"识别组{group_index+1} 截图失败或为空")
                return

            region_w = right - left
            region_h = bottom - top
            self.app.logging_manager.debug("OCR", f"识别组{group_index+1} 截图成功: 尺寸={screenshot.size}, 模式={screenshot.mode}")
            self.app.logging_manager.log_message(f"识别组{group_index+1}: 截图完成 ({region_w}x{region_h})")

            current_hash = imagehash.average_hash(screenshot.resize((64, 64)))
            
            if current_hash == last_hashes.get(group_index) and frame_counts.get(group_index, 0) % 5 != 0:
                frame_counts[group_index] += 1
                return
            
            last_hashes[group_index] = current_hash
            frame_counts[group_index] += 1

            start_time = time.time()

            processed_image = _preprocess_image(screenshot, group_index)
            if not processed_image:
                self.app.logging_manager.error("OCR", f"识别组{group_index+1}: 图像预处理失败")
                self.app.logging_manager.debug("OCR", f"识别组{group_index+1} 图像预处理失败")
                return

            rec = self._recognize_on_processed_image(
                processed_image, group_index, keywords_str, current_lang,
                click_enabled, left, top, right, bottom, log_results=True,
            )
            elapsed_time = time.time() - start_time
            sleep_time = max(0.01, 0.1 - elapsed_time)
            time.sleep(sleep_time)

            if rec.get("matched"):
                if click_enabled and rec.get("click_pos"):
                    click_pos = rec["click_pos"]
                    self.app.logging_manager.log_message(
                        f"识别组{group_index+1}: 点击位置 ({click_pos[0]}, {click_pos[1]})"
                    )
                self.execute_group_actions(group, group_index, rec, for_test=False)
            elif keywords_str:
                self.app.logging_manager.log_message(f"识别组{group_index+1}: 未匹配到关键词")

        except Exception as e:
            self.app.logging_manager.error("OCR", f"识别组{group_index+1}错误: 未知错误 - {str(e)}")
            import traceback
            self.app.logging_manager.error("OCR", f"错误详情: {traceback.format_exc()}")
        finally:
            if processed_image is not None:
                del processed_image
            if screenshot is not None:
                screenshot.close()
                del screenshot
    
    def _validate_trigger_input(self, group, group_index):
        if not group:
            self.app.logging_manager.error("OCR", f"识别组{group_index+1}错误: 组配置为空")
            return False, None, None, None

        key = safe_group_get(group, "key", "")
        alarm_enabled = safe_group_get(group, "alarm", False)
        region = group.get("region")

        if not key:
            self.app.logging_manager.log_message(f"识别组{group_index+1}警告: 未设置触发按键")

        return True, key, alarm_enabled, region
    
    def _calculate_click_position(self, click_pos, region, group_index):
        if click_pos is not None:
            return click_pos

        if not region:
            self.app.logging_manager.error("OCR", f"识别组{group_index+1}错误: 未设置识别区域，无法计算点击位置")
            return None, None

        try:
            x1, y1, x2, y2 = region
            click_x = (x1 + x2) // 2
            click_y = (y1 + y2) // 2
            return click_x, click_y
        except (ValueError, TypeError) as e:
            self.app.logging_manager.error("OCR", f"识别组{group_index+1}错误: 区域坐标无效 - {str(e)}")
            return None, None
    
    def _execute_key_press(self, key, group_index, *, for_test=False):
        if not for_test and (not self.app.is_running or getattr(self.app, 'system_stopped', False)):
            return

        if not key:
            return

        group = self.app.ocr_groups[group_index]
        
        from modules.input import KeyEventExecutor
        delay_min_var = group["delay_min"]
        delay_max_var = group["delay_max"]
        executor = KeyEventExecutor(self.app.input_controller, delay_min_var, delay_max_var, self.PRIORITY)
        executor.execute_keypress(key)
        
        self.app.logging_manager.log_message(f"识别组{group_index+1}按下了 {key} 键")
        self.last_trigger_times[group_index] = time.time()
    
    def _play_alarm_if_enabled(self, alarm_enabled, group_index):
        try:
            if alarm_enabled:
                from core.config import ConfigVar
                temp_alarm_var = ConfigVar(True)
                self.app.alarm_module.play_alarm_sound(temp_alarm_var)
        except Exception as e:
            self.app.logging_manager.error("OCR", f"识别组{group_index+1}错误: 播放报警声音失败 - {str(e)}")
    
    def trigger_action_for_group(self, group, group_index, click_enabled, click_pos=None, *, for_test=False):
        try:
            if not for_test and (not self.app.is_running or getattr(self.app, 'system_stopped', False)):
                return

            valid, key, alarm_enabled, region = self._validate_trigger_input(group, group_index)
            if not valid:
                return

            self.app.logging_manager.log_message(f"识别组{group_index+1}触发动作，按键: {key}")

            if click_enabled:
                click_x, click_y = self._calculate_click_position(click_pos, region, group_index)
                offset_range = int(safe_group_get(group, "click_offset", "0"))
                self.click_handler.execute_click(
                    x=click_x,
                    y=click_y,
                    priority=self.PRIORITY,
                    module_name="识别组",
                    index=group_index,
                    offset_range=offset_range,
                    for_test=for_test,
                )

            self._execute_key_press(key, group_index, for_test=for_test)
        except Exception as e:
            self.app.logging_manager.error("OCR", f"识别组{group_index+1}错误: 触发动作失败 - {str(e)}")
            import traceback
            self.app.logging_manager.error("OCR", f"错误详情: {traceback.format_exc()}")

        if 'alarm_enabled' in locals():
            self._play_alarm_if_enabled(alarm_enabled, group_index)
