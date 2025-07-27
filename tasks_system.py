import json
import os
import time
import random
from datetime import datetime, timedelta

TASKS_FILE = "user_tasks.json"

class TasksSystem:
    def __init__(self):
        self.tasks_file = TASKS_FILE

    def load_user_tasks(self, user_id):
        """تحميل مهام المستخدم"""
        if not os.path.exists(self.tasks_file):
            return {"active_tasks": [], "completed_tasks": [], "last_update": 0}

        try:
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(str(user_id), {"active_tasks": [], "completed_tasks": [], "last_update": 0})
        except (json.JSONDecodeError, FileNotFoundError):
            return {"active_tasks": [], "completed_tasks": [], "last_update": 0}

    def save_user_tasks(self, user_id, tasks_data):
        """حفظ مهام المستخدم"""
        if not os.path.exists(self.tasks_file):
            data = {}
        else:
            try:
                with open(self.tasks_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                data = {}

        data[str(user_id)] = tasks_data

        with open(self.tasks_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def generate_daily_tasks(self, user_id):
        """توليد مهام يومية جديدة"""
        task_templates = [
            {
                "name": "جمع الذهب اليومي",
                "description": "اجمع 50 ذهب من أي مصدر",
                "type": "collect_gold",
                "target": 50,
                "difficulty": "سهل",
                "reward": {"دولار": 50000, "exp": 100},
                "category": "daily"
            },
            {
                "name": "شراء من المتجر",
                "description": "اشتر 10 عناصر من المتجر",
                "type": "buy_items",
                "target": 10,
                "difficulty": "متوسط",
                "reward": {"دولار": 100000, "ذهب": 20, "exp": 200},
                "category": "daily"
            },
            {
                "name": "صياد ماهر",
                "description": "اصطد 15 سمكة",
                "type": "catch_fish",
                "target": 15,
                "difficulty": "متوسط",
                "reward": {"دولار": 75000, "exp": 150},
                "category": "daily"
            },
            {
                "name": "مزارع مجتهد",
                "description": "احصد 5 محاصيل",
                "type": "harvest_crops",
                "target": 5,
                "difficulty": "سهل",
                "reward": {"دولار": 60000, "exp": 120},
                "category": "daily"
            },
            {
                "name": "لاعب محترف",
                "description": "اربح في 3 ألعاب مختلفة",
                "type": "win_games",
                "target": 3,
                "difficulty": "صعب",
                "reward": {"دولار": 150000, "ذهب": 30, "exp": 300},
                "category": "daily"
            }
        ]

        # اختيار 3 مهام عشوائية
        selected_tasks = random.sample(task_templates, 3)

        for task in selected_tasks:
            task["id"] = f"{user_id}_{int(time.time())}_{random.randint(1000, 9999)}"
            task["progress"] = 0
            task["completed"] = False
            task["created_at"] = time.time()
            task["expires_at"] = time.time() + (24 * 3600)  # 24 ساعة

        return selected_tasks

    def check_and_update_tasks(self, user_id):
        """فحص وتحديث المهام"""
        user_tasks = self.load_user_tasks(user_id)
        current_time = time.time()

        # فحص انتهاء صلاحية المهام
        active_tasks = []
        for task in user_tasks.get("active_tasks", []):
            if task["expires_at"] > current_time:
                active_tasks.append(task)

        # إنشاء مهام جديدة إذا لزم الأمر
        if len(active_tasks) < 3:
            new_tasks = self.generate_daily_tasks(user_id)
            active_tasks.extend(new_tasks)

        user_tasks["active_tasks"] = active_tasks
        user_tasks["last_update"] = current_time

        self.save_user_tasks(user_id, user_tasks)
        return user_tasks

    def update_task_progress(self, user_id, task_type, amount=1):
        """تحديث تقدم المهام"""
        user_tasks = self.load_user_tasks(user_id)
        completed_tasks = []

        for task in user_tasks.get("active_tasks", []):
            if task["type"] == task_type and not task["completed"]:
                task["progress"] = min(task["target"], task["progress"] + amount)

                if task["progress"] >= task["target"]:
                    task["completed"] = True
                    completed_tasks.append(task)

        if completed_tasks:
            self.save_user_tasks(user_id, user_tasks)

        return completed_tasks

    def claim_task_reward(self, user_id, task_id):
        """استلام مكافأة المهمة"""
        from data_utils import load_data, save_data

        user_tasks = self.load_user_tasks(user_id)

        for task in user_tasks.get("active_tasks", []):
            if task["id"] == task_id and task["completed"] and not task.get("claimed", False):
                # إضافة المكافآت
                data = load_data()
                user = data.get(str(user_id), {})

                for currency, amount in task["reward"].items():
                    if currency == "exp":
                        user["experience"] = user.get("experience", 0) + amount
                        self._update_experience_level(user)
                    else:
                        user.setdefault("balance", {})[currency] = user["balance"].get(currency, 0) + amount

                data[str(user_id)] = user
                save_data(data)

                # تحديث حالة المهمة
                task["claimed"] = True
                self.save_user_tasks(user_id, user_tasks)

                return task["reward"]

        return None

    def _update_experience_level(self, user_data):
        """تحديث مستوى المستخدم حسب الخبرة"""
        experience = user_data.get("experience", 0)
        current_level = user_data.get("level", 1)

        # حساب المستوى الجديد
        new_level = 1
        exp_needed = 0

        while exp_needed <= experience:
            exp_for_next = new_level * 1000  # 1000 خبرة لكل مستوى
            if exp_needed + exp_for_next > experience:
                break
            exp_needed += exp_for_next
            new_level += 1

        user_data["level"] = new_level

    def get_user_level_info(self, user_id):
        """جلب معلومات مستوى المستخدم"""
        from data_utils import load_data

        data = load_data()
        user = data.get(str(user_id), {})

        experience = user.get("experience", 0)
        level = user.get("level", 1)

        # حساب الخبرة المطلوبة للمستوى التالي
        exp_for_current_level = sum(i * 1000 for i in range(1, level))
        exp_for_next_level = level * 1000
        exp_progress = experience - exp_for_current_level

        return {
            "level": level,
            "experience": experience,
            "exp_progress": exp_progress,
            "exp_for_next_level": exp_for_next_level,
            "exp_needed": max(0, exp_for_next_level - exp_progress)
        }

# إنشاء كائن عام للنظام
tasks_system = TasksSystem()